"""Telegram handlers for bot commands and user messages."""

from datetime import datetime
from typing import TypeAlias, cast

from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from calendar_bot import sql_storage
from calendar_bot.config import Config
from calendar_bot.events import Event
from calendar_bot.exceptions import EventTimeError
from calendar_bot.telegram.formatters import format_event_card
from calendar_bot.telegram.keyboards import (
    ADD_EVENT_BUTTON,
    CANCEL_EVENT_CALLBACK,
    DELETE_EVENT_BUTTON,
    DELETE_EVENT_CALLBACK_PREFIX,
    LIST_EVENTS_BUTTON,
    SAVE_EVENT_CALLBACK,
    delete_events_keyboard,
    event_confirmation_keyboard,
    main_menu_keyboard,
)
from calendar_bot.llm_parser import parse_event
from calendar_bot.telegram.utils import cancelable


EventDraftData: TypeAlias = dict[str, str | None]


class EventDraftState(StatesGroup):
    """FSM states used by the event draft confirmation flow."""

    waiting_for_confirmation = State()


def register_telegram_handlers(dp: Dispatcher, config: Config) -> None:
    """Register all Telegram message handlers on the dispatcher."""

    @dp.message(CommandStart())
    async def start_handler(message: Message) -> None:
        """Send a short greeting when the user starts the bot."""

        await message.answer(
            "Привет! Я CalendarBot. Напиши событие обычной фразой, "
            "а я предложу черновик перед сохранением.",
            reply_markup=main_menu_keyboard(),
        )

    @dp.message(Command("list"))
    @dp.message(F.text == LIST_EVENTS_BUTTON)
    async def list_handler(message: Message) -> None:
        """Show current events for the Telegram user."""

        await _send_events_list(message, config)

    @dp.message(Command("delete"))
    @dp.message(F.text == DELETE_EVENT_BUTTON)
    async def delete_handler(message: Message) -> None:
        """Show current events with inline delete buttons."""

        if message.from_user is None:
            await message.answer("Возникла ошибка при обработке автора сообщения.")
            return

        user_id = message.from_user.id
        sql_storage.delete_expired_events(config.database_path, datetime.now())
        events_list = sql_storage.list_events(config.database_path, user_id)

        if not events_list:
            await message.answer("Текущих событий пока нет.", reply_markup=main_menu_keyboard())
            return

        await message.answer(
            "Выбери событие для удаления:",
            reply_markup=delete_events_keyboard(events_list),
        )

    @dp.callback_query(F.data.startswith(DELETE_EVENT_CALLBACK_PREFIX))
    async def delete_event_callback_handler(callback: CallbackQuery) -> None:
        """Delete the event selected by an inline button."""

        if callback.data is None:
            await callback.answer("Не удалось обработать действие.", show_alert=True)
            return

        event_id_text = callback.data.removeprefix(DELETE_EVENT_CALLBACK_PREFIX)
        if not event_id_text.isdigit():
            await callback.answer("Не удалось определить событие.", show_alert=True)
            return

        deleted = sql_storage.delete_event(
            config.database_path,
            callback.from_user.id,
            int(event_id_text),
        )

        if deleted:
            await callback.answer("Событие удалено.")
            if isinstance(callback.message, Message):
                await callback.message.edit_text("Событие удалено.")
        else:
            await callback.answer("Событие уже удалено или не найдено.", show_alert=True)

    @dp.message(F.text == ADD_EVENT_BUTTON)
    async def add_event_hint_handler(message: Message) -> None:
        """Explain how to add an event from natural language."""

        await message.answer(
            "Напиши событие одной фразой. Например: завтра в 15:00 "
            "встреча с преподавателем на час."
        )

    @dp.message(Command("cancel"))
    async def cancel_handler(message: Message, state: FSMContext) -> None:
        """Cancel the current action if there is one."""

        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_menu_keyboard())

    @dp.callback_query(F.data == SAVE_EVENT_CALLBACK)
    async def save_event_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
        """Save a confirmed event draft."""

        data = await state.get_data()
        pending_event = data.get("pending_event")

        if not isinstance(pending_event, dict):
            await callback.answer("Черновик события не найден.", show_alert=True)
            await state.clear()
            return

        try:
            event = _event_from_dict(
                callback.from_user.id,
                cast(EventDraftData, pending_event),
            )
        except (KeyError, ValueError, EventTimeError):
            await callback.answer(
                "Черновик повреждён. Попробуй создать событие заново.",
                show_alert=True,
            )
            await state.clear()
            return

        sql_storage.add_event(config.database_path, event)
        await state.clear()
        await callback.answer("Событие сохранено.")

        if isinstance(callback.message, Message):
            await callback.message.edit_text("Событие сохранено:\n\n" + format_event_card(event))

    @dp.callback_query(F.data == CANCEL_EVENT_CALLBACK)
    async def cancel_event_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
        """Discard a parsed event draft."""

        await state.clear()
        await callback.answer("Черновик отменён.")

        if isinstance(callback.message, Message):
            await callback.message.edit_text("Черновик отменён.")

    @dp.message(EventDraftState.waiting_for_confirmation)
    @cancelable
    async def waiting_for_confirmation_handler(message: Message, state: FSMContext) -> None:
        """Remind the user to confirm or cancel the current event draft."""

        await message.answer("Сначала подтверди или отмени текущий черновик кнопками под сообщением.")

    @dp.message()
    async def text_handler(message: Message, state: FSMContext) -> None:
        """Parse a free-form text message and show it as an event draft."""

        await _parse_and_send_event_draft(message, state, config)


async def _parse_and_send_event_draft(message: Message, state: FSMContext, config: Config) -> None:
    """Parse a user message and ask for confirmation before saving."""

    text = message.text

    if text is None:
        await message.answer("Пока поддерживается работа только с текстовыми сообщениями.")
        return

    if message.from_user is None:
        await message.answer("Возникла ошибка при обработке автора сообщения.")
        return

    try:
        parsed_event = await parse_event(text, config.openai_api_key)
    except Exception:
        await message.answer("Не получилось разобрать событие. Попробуй описать его точнее.")
        return

    if parsed_event.confidence <= 0.5:
        await message.answer("Событие получилось неоднозначным. Добавь дату, время или действие точнее.")
        return

    try:
        event = Event.from_parsed(message.from_user.id, parsed_event)
    except EventTimeError:
        await message.answer("Не получилось определить корректное время события.")
        return

    await state.update_data(pending_event=_event_to_dict(event))
    await state.set_state(EventDraftState.waiting_for_confirmation)

    await message.answer(
        format_event_card(event),
        reply_markup=event_confirmation_keyboard(),
    )


async def _send_events_list(message: Message, config: Config) -> None:
    """Send a formatted list of active events."""

    if message.from_user is None:
        await message.answer("Возникла ошибка при обработке автора сообщения.")
        return

    user_id = message.from_user.id
    sql_storage.delete_expired_events(config.database_path, datetime.now())
    events_list = sql_storage.list_events(config.database_path, user_id)

    if not events_list:
        await message.answer("Текущих событий пока нет.", reply_markup=main_menu_keyboard())
        return

    event_cards = [format_event_card(event) for event in events_list]
    await message.answer(
        "Текущие события:\n\n" + "\n\n".join(event_cards),
        reply_markup=main_menu_keyboard(),
    )


def _event_to_dict(event: Event) -> EventDraftData:
    """Serialize an event draft for FSM storage."""

    return {
        "title": event.title,
        "start_at": event.start_at.isoformat(),
        "end_at": event.end_at.isoformat(),
        "description": event.description,
        "location": event.location,
    }


def _event_from_dict(user_id: int, data: EventDraftData) -> Event:
    """Restore an event draft from FSM storage."""

    return Event(
        user_id=user_id,
        title=_required_string(data["title"]),
        start_at=datetime.fromisoformat(_required_string(data["start_at"])),
        end_at=datetime.fromisoformat(_required_string(data["end_at"])),
        description=data["description"],
        location=data["location"],
    )


def _required_string(value: str | None) -> str:
    """Return a required string field or raise ValueError."""

    if value is None:
        raise ValueError("Required string is missing")

    return value

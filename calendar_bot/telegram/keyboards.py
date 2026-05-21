"""Telegram keyboard builders."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from calendar_bot.events import Event


ADD_EVENT_BUTTON = "Добавить событие"
LIST_EVENTS_BUTTON = "Мои события"
DELETE_EVENT_BUTTON = "Удалить событие"

SAVE_EVENT_CALLBACK = "event:save"
CANCEL_EVENT_CALLBACK = "event:cancel"
DELETE_EVENT_CALLBACK_PREFIX = "delete:"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build the persistent Telegram menu keyboard."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADD_EVENT_BUTTON)],
            [
                KeyboardButton(text=LIST_EVENTS_BUTTON),
                KeyboardButton(text=DELETE_EVENT_BUTTON),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Опиши событие или выбери действие",
    )


def event_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Build inline buttons for saving or discarding a parsed event draft."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Сохранить", callback_data=SAVE_EVENT_CALLBACK),
                InlineKeyboardButton(text="Отмена", callback_data=CANCEL_EVENT_CALLBACK),
            ]
        ]
    )


def delete_events_keyboard(events_list: list[Event]) -> InlineKeyboardMarkup:
    """Build inline delete buttons for visible events."""

    buttons: list[list[InlineKeyboardButton]] = []
    for event in events_list:
        if event.id is None:
            continue

        title = event.title
        if len(title) > 40:
            title = title[:37] + "..."

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"Удалить: {title}",
                    callback_data=f"{DELETE_EVENT_CALLBACK_PREFIX}{event.id}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)

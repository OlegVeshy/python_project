from datetime import datetime

from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from calendar_bot.llm_parser import parse_event
from calendar_bot.config import Config
from calendar_bot.events import Event
from calendar_bot import sql_storage
from calendar_bot import telegram_utils


class DeleteEventState(StatesGroup):
    waiting_for_event_id = State()


def register_telegram_handlers(dp: Dispatcher, config: Config) -> None:
    @dp.message(CommandStart())
    async def start_handler(message: Message) -> None:
        await message.answer("Привет! Я CalendarBot.")

    @dp.message(Command("list"))
    async def list_handler(message: Message) -> None:
        if message.from_user is None:
            await message.answer("Возникла ошибка при обработке автора сообщения.")
            return 
        
        user_id = message.from_user.id
        sql_storage.delete_expired_events(config.database_path, datetime.now())
        events_list = sql_storage.list_events(config.database_path, user_id)

        if not events_list:
            await message.answer("Текущих событий пока нет")
            return

        answer = "==== Текущие события ====\n"
        for event in events_list:
            answer += event.__str__()
        
        await message.answer(answer)

    @dp.message(Command("delete"))
    async def delete_handler(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            await message.answer("Возникла ошибка при обработке автора сообщения.")
            return

        user_id = message.from_user.id
        sql_storage.delete_expired_events(config.database_path, datetime.now())
        events_list = sql_storage.list_events(config.database_path, user_id)

        if not events_list:
            await message.answer("Текущих событий пока нет.")
            return

        event_ids = [event.id for event in events_list]
        await state.update_data(event_ids=event_ids)

        answer = "Введите номер события, которое нужно удалить:\n"
        for number, event in enumerate(events_list, start=1):
            answer += f"{number}. {event.title}\n"

        await message.answer(answer)
        await state.set_state(DeleteEventState.waiting_for_event_id)

    @dp.message(DeleteEventState.waiting_for_event_id)
    @telegram_utils.cancelable
    async def delete_event_id_handler(message: Message, state: FSMContext) -> None:
        text = message.text

        if text is None or not text.isdigit():
            await message.answer("Номер события должен быть числом. Попробуйте ещё раз.")
            return

        if message.from_user is None:
            await message.answer("Возникла ошибка при обработке автора сообщения.")
            await state.clear()
            return

        selected_number = int(text)
        data = await state.get_data()
        event_ids = data.get("event_ids", [])

        if selected_number < 1 or selected_number > len(event_ids):
            await message.answer("События с таким номером нет. Попробуйте ещё раз.")
            return

        event_id = event_ids[selected_number - 1]
        if event_id is None:
            await message.answer("Не удалось определить id события.")
            await state.clear()
            return

        user_id = message.from_user.id
        deleted = sql_storage.delete_event(config.database_path, user_id, event_id)

        if deleted:
            await message.answer("Событие удалено.")
        else:
            await message.answer("Событие не найдено.")

        await state.clear()

    @dp.message()
    async def text_handler(message: Message) -> None:
        text = message.text

        if text is None:
            await message.answer("Пока поддерживается работа только с текстовыми сообщениями.")
            return
        
        if message.from_user is None:
            await message.answer("Возникла ошибка при обработке автора сообщения.")
            return
        
        user_id = message.from_user.id
        parsed_event = parse_event(text, config.openai_api_key)

        if parsed_event.confidence <= 0.5:
            await message.answer("Событие не получилось обработать в силу неоднозначности.")
            return

        event = Event.from_parsed(user_id, parsed_event)
        database_path = config.database_path

        sql_storage.add_event(database_path, event)
        await message.answer("Cобытие успешно добавлено")

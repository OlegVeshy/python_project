from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from calendar_bot.llm_parser import parse_event
from calendar_bot.config import Config, load_config
from calendar_bot.events import Event
from calendar_bot import sql_storage

def register_telegram_handlers(dp: Dispatcher, config: Config) -> None:
    @dp.message(CommandStart())
    async def start_handler(message: Message) -> None:
        await message.answer("Привет! Я CalendarBot.")
    
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

        event = Event.from_parsed(user_id, parsed_event)
        database_path = load_config().database_path

        sql_storage.add_event(database_path, event)
        await message.answer("Cобытие успешно добавлено")

        





    


        

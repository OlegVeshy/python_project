from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from calendar_bot.llm_parser import parse_event
from calendar_bot.config import Config


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

        parsed_event = parse_event(text, config.openai_api_key)
        # TODO: сохранить событие в базу после подключения SQLite storage.
        await message.answer(
            f"Название: {parsed_event.title}\n"
            f"Начало: {parsed_event.start_at}\n"
            f"Конец: {parsed_event.end_at}\n"
            f"Место: {parsed_event.location or 'не указано'}\n"
            f"Уверенность: {parsed_event.confidence:.2f}"
        )

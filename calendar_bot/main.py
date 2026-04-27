import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from calendar_bot.config import load_config


config = load_config()

bot = Bot(token=config.telegram_bot_token)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer("Привет! Я CalendarBot.")


async def main() -> None:
    await dp.start_polling(bot)
 

if __name__ == "__main__":
    asyncio.run(main())

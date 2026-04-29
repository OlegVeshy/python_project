"""Application entry point for CalendarBot."""

import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher

from calendar_bot.config import load_config
from calendar_bot.telegram_handlers import register_telegram_handlers
from calendar_bot import sql_storage


config = load_config()

bot = Bot(token=config.telegram_bot_token)
dp = Dispatcher()

register_telegram_handlers(dp, config)


async def main() -> None:
    """Prepare storage and start Telegram polling."""

    sql_storage.init_db(config.database_path)
    sql_storage.delete_expired_events(config.database_path, datetime.now())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

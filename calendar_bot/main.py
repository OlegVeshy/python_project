"""Application entry point for CalendarBot."""

import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from calendar_bot import sql_storage
from calendar_bot.config import load_config
from calendar_bot.reminders import reminder_loop
from calendar_bot.telegram.handlers import register_telegram_handlers


async def main() -> None:
    """Prepare storage and start Telegram polling."""

    config = load_config()
    bot = Bot(token=config.telegram_bot_token)
    dp = Dispatcher()

    register_telegram_handlers(dp, config)

    sql_storage.init_db(config.database_path)
    sql_storage.delete_expired_events(config.database_path, datetime.now())
    asyncio.create_task(reminder_loop(bot, config.database_path))

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Открыть меню"),
            BotCommand(command="list", description="Показать события"),
            BotCommand(command="delete", description="Удалить событие"),
            BotCommand(command="cancel", description="Отменить текущее действие"),
        ]
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

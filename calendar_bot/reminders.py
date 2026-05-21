"""Background reminder sender."""

import asyncio
from datetime import datetime

from aiogram import Bot

from calendar_bot import sql_storage
from calendar_bot.telegram.formatters import format_event_card


async def reminder_loop(bot: Bot, database_path: str) -> None:
    """Periodically send reminders for upcoming events."""

    while True:
        now = datetime.now()
        events = sql_storage.list_due_reminders(database_path, now)

        for event in events:
            if event.id is None:
                continue

            await bot.send_message(
                event.user_id,
                "Напоминание: скоро событие.\n\n" + format_event_card(event),
            )
            sql_storage.mark_event_reminded(database_path, event.id, now)

        await asyncio.sleep(60)

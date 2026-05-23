"""Telegram message formatting helpers."""

from datetime import datetime

from calendar_bot.events import Event


def format_event_card(event: Event) -> str:
    """Format an event as a compact Telegram card."""

    lines = [
        event.title,
        f"Начало: {format_datetime(event.start_at)}",
    ]

    if event.is_instant:
        lines.append("Тип: моментальное событие")
    else:
        lines.append(f"Конец: {format_datetime(event.end_at)}")
        lines.append(f"Длительность: {event.duration_minutes} мин.")

    if event.location is not None:
        lines.append(f"Место: {event.location}")

    if event.description is not None:
        lines.append(f"Описание: {event.description}")

    return "\n".join(lines)


def format_datetime(value: datetime) -> str:
    """Format a datetime for Russian Telegram messages."""

    return value.strftime("%d.%m.%Y %H:%M")

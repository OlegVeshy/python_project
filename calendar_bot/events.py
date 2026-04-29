"""Domain models used by CalendarBot."""

from dataclasses import dataclass
from datetime import datetime

from calendar_bot.exceptions import EventTimeError


@dataclass
class ParsedEvent:
    """Event data returned by the LLM before it is linked to a Telegram user."""

    title: str
    start_at: datetime
    end_at: datetime
    description: str | None = None
    location: str | None = None
    confidence: float = 1.0


@dataclass
class Event:
    """Calendar event owned by a specific Telegram user."""

    user_id: int
    title: str
    start_at: datetime
    end_at: datetime
    description: str | None = None
    location: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        """Validate that event time range is not negative."""

        if self.end_at < self.start_at:
            raise EventTimeError("Event end time cannot be earlier than start time")

    @property
    def duration_minutes(self) -> int:
        """Return event duration in full minutes."""

        return int((self.end_at - self.start_at).total_seconds() // 60)

    @property
    def is_instant(self) -> bool:
        """Return whether the event has zero duration."""

        return self.start_at == self.end_at

    @classmethod
    def from_parsed(cls, user_id: int, parsed_event: ParsedEvent) -> "Event":
        """Create a user-owned event from LLM parsing result."""

        return cls(
            user_id=user_id,
            title=parsed_event.title,
            start_at=parsed_event.start_at,
            end_at=parsed_event.end_at,
            description=parsed_event.description,
            location=parsed_event.location,
        )

    def __str__(self) -> str:
        """Format event for Telegram messages."""

        lines = [
            f"-> {self.title} <-",
            f"Начало: {self.start_at}",
            f"Конец: {self.end_at}",
        ]

        if self.is_instant:
            lines.append("Тип: моментальное событие")
        else:
            lines.append(f"Длительность: {self.duration_minutes} мин.")

        if self.location is not None:
            lines.append(f"Место: {self.location}")

        if self.description is not None:
            lines.append(self.description)

        return "\n".join(lines) + "\n"

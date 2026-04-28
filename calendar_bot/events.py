from dataclasses import dataclass
from datetime import datetime

from calendar_bot.exceptions import EventTimeError


@dataclass
class ParsedEvent:
    title: str
    start_at: datetime
    end_at: datetime
    description: str | None = None
    location: str | None = None
    confidence: float = 1.0


@dataclass
class Event:
    user_id: int
    title: str
    start_at: datetime
    end_at: datetime
    description: str | None = None
    location: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if self.end_at < self.start_at:
            raise EventTimeError("Event end time cannot be earlier than start time")

    @classmethod
    def from_parsed(cls, user_id: int, parsed_event: ParsedEvent) -> "Event":
        return cls(
            user_id=user_id,
            title=parsed_event.title,
            start_at=parsed_event.start_at,
            end_at=parsed_event.end_at,
            description=parsed_event.description,
            location=parsed_event.location,
        )
    
    def __str__(self):
        return f"""
-> {self.title} <-
Начало: {self.start_at}
Конец: {self.end_at} \
{'' if self.location is None else "\nМесто: " + self.location} \
{'' if self.description is None else "\n" + self.description}
        """



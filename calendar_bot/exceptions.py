class CalendarBotError(Exception):
    """Base class for CalendarBot expected errors."""


class ConfigError(CalendarBotError):
    """Raised when application configuration is invalid."""


class EventError(CalendarBotError):
    """Base class for errors associated with events."""


class EventTimeError(EventError):
    """Raised when event end time is earlier than start time."""

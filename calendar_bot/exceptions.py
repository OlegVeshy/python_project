class CalendarBotError(Exception):
    """Base class for CalendarBot expected errors."""


class ConfigError(CalendarBotError):
    """Raised when application configuration is invalid."""

"""SQLite persistence functions for calendar events."""

import sqlite3
from datetime import datetime, timedelta

from calendar_bot.events import Event


REMINDER_MINUTES = 30


CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    start_at TEXT NOT NULL,
    end_at TEXT NOT NULL,
    description TEXT,
    location TEXT,
    remind_at TEXT,
    reminded_at TEXT
);
"""

INSERT_EVENT = """
INSERT INTO events(
    user_id, title, start_at, end_at, description, location, remind_at
)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

LIST_EVENTS = """
SELECT id, user_id, title, start_at, end_at, description, location
FROM events
WHERE user_id = ?
ORDER BY start_at
"""

DELETE_EVENT = """
DELETE FROM events
WHERE id = ? AND user_id = ?
"""

DELETE_EXPIRED_EVENTS = """
DELETE FROM events
WHERE end_at < ?
"""

LIST_DUE_REMINDERS = """
SELECT id, user_id, title, start_at, end_at, description, location
FROM events
WHERE reminded_at IS NULL
  AND remind_at <= ?
  AND start_at > ?
ORDER BY start_at
"""

MARK_EVENT_REMINDED = """
UPDATE events
SET reminded_at = ?
WHERE id = ?
"""


def init_db(database_path: str) -> None:
    """Create the events table if the database is empty."""

    with sqlite3.connect(database_path) as connection:
        connection.execute(CREATE_EVENTS_TABLE)
        _add_column_if_missing(connection, "remind_at", "TEXT")
        _add_column_if_missing(connection, "reminded_at", "TEXT")


def add_event(database_path: str, event: Event) -> None:
    """Save an event to SQLite."""

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            INSERT_EVENT,
            (
                event.user_id,
                event.title,
                event.start_at.isoformat(),
                event.end_at.isoformat(),
                event.description,
                event.location,
                _remind_at(event).isoformat(),
            ),
        )


def list_events(database_path: str, user_id: int) -> list[Event]:
    """Return all events belonging to a Telegram user."""

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(LIST_EVENTS, (user_id,)).fetchall()

    events = []
    for row in rows:
        events.append(
            Event(
                id=row[0],
                user_id=row[1],
                title=row[2],
                start_at=datetime.fromisoformat(row[3]),
                end_at=datetime.fromisoformat(row[4]),
                description=row[5],
                location=row[6],
            )
        )

    return events


def delete_event(database_path: str, user_id: int, event_id: int) -> bool:
    """Delete a user's event by database id and report whether it existed."""

    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(DELETE_EVENT, (event_id, user_id))
        deleted = cursor.rowcount > 0

    return deleted


def delete_expired_events(database_path: str, now: datetime) -> int:
    """Delete events that ended before the given datetime."""

    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(DELETE_EXPIRED_EVENTS, (_to_local_naive(now).isoformat(),))
        deleted_count = cursor.rowcount

    return deleted_count


def list_due_reminders(database_path: str, now: datetime) -> list[Event]:
    """Return events that need a reminder now."""

    normalized_now = _to_local_naive(now).isoformat()
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            LIST_DUE_REMINDERS,
            (normalized_now, normalized_now),
        ).fetchall()

    events = []
    for row in rows:
        events.append(
            Event(
                id=row[0],
                user_id=row[1],
                title=row[2],
                start_at=datetime.fromisoformat(row[3]),
                end_at=datetime.fromisoformat(row[4]),
                description=row[5],
                location=row[6],
            )
        )

    return events


def mark_event_reminded(database_path: str, event_id: int, reminded_at: datetime) -> None:
    """Mark an event reminder as sent."""

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            MARK_EVENT_REMINDED,
            (_to_local_naive(reminded_at).isoformat(), event_id),
        )


def _to_local_naive(value: datetime) -> datetime:
    """Convert aware datetimes to local naive datetimes used by storage."""

    if value.tzinfo is None:
        return value

    return value.astimezone().replace(tzinfo=None)


def _remind_at(event: Event) -> datetime:
    """Return the reminder time for an event."""

    return event.start_at - timedelta(minutes=REMINDER_MINUTES)


def _add_column_if_missing(
    connection: sqlite3.Connection,
    column_name: str,
    column_type: str,
) -> None:
    """Add a column to existing databases if it is missing."""

    columns = [row[1] for row in connection.execute("PRAGMA table_info(events)")]
    if column_name not in columns:
        connection.execute(f"ALTER TABLE events ADD COLUMN {column_name} {column_type}")

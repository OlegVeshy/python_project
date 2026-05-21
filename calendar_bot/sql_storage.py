"""SQLite persistence functions for calendar events."""

import sqlite3
from datetime import datetime

from calendar_bot.events import Event


CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    start_at TEXT NOT NULL,
    end_at TEXT NOT NULL,
    description TEXT,
    location TEXT
);
"""

INSERT_EVENT = """
INSERT INTO events(
    user_id, title, start_at, end_at, description, location
)
VALUES (?, ?, ?, ?, ?, ?)
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

DELETE_EVENT_BY_ID = """
DELETE FROM events
WHERE id = ?
"""

LIST_EVENT_ENDS = """
SELECT id, end_at
FROM events
"""


def init_db(database_path: str) -> None:
    """Create the events table if the database is empty."""

    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute(CREATE_EVENTS_TABLE)

    connection.commit()
    connection.close()


def add_event(database_path: str, event: Event) -> None:
    """Save an event to SQLite."""

    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute(
        INSERT_EVENT,
        (
            event.user_id,
            event.title,
            event.start_at.isoformat(),
            event.end_at.isoformat(),
            event.description,
            event.location,
        ),
    )

    connection.commit()
    connection.close()


def list_events(database_path: str, user_id: int) -> list[Event]:
    """Return all events belonging to a Telegram user."""

    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute(LIST_EVENTS, (user_id,))
    rows_list = cursor.fetchall()
    event_list = []

    for row in rows_list:
        event = Event(
            id=row[0],
            user_id=row[1],
            title=row[2],
            start_at=datetime.fromisoformat(row[3]),
            end_at=datetime.fromisoformat(row[4]),
            description=row[5],
            location=row[6],
        )

        event_list.append(event)

    connection.close()
    return event_list


def delete_event(database_path: str, user_id: int, event_id: int) -> bool:
    """Delete a user's event by database id and report whether it existed."""

    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute(DELETE_EVENT, (event_id, user_id))
    deleted = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return deleted


def delete_expired_events(database_path: str, now: datetime) -> int:
    """Delete events that ended before the given datetime."""

    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    normalized_now = _to_local_naive(now)
    cursor.execute(LIST_EVENT_ENDS)

    deleted_count = 0
    for event_id, end_at_text in cursor.fetchall():
        end_at = _parse_stored_datetime(end_at_text)
        if end_at < normalized_now:
            cursor.execute(DELETE_EVENT_BY_ID, (event_id,))
            deleted_count += cursor.rowcount

    connection.commit()
    connection.close()

    return deleted_count


def _parse_stored_datetime(value: str) -> datetime:
    """Parse stored datetime and normalize timezone-aware values to local naive time."""

    return _to_local_naive(datetime.fromisoformat(value))


def _to_local_naive(value: datetime) -> datetime:
    """Convert aware datetimes to local naive datetimes used by storage."""

    if value.tzinfo is None:
        return value

    return value.astimezone().replace(tzinfo=None)

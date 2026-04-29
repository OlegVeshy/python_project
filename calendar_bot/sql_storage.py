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
WHERE user_id = (?)
ORDER BY start_at
"""

DELETE_EVENT = """
DELETE FROM events
WHERE id = ? AND user_id = ?
"""


def init_db(database_path: str) -> None:
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute(CREATE_EVENTS_TABLE)

    connection.commit()
    connection.close()


def add_event(database_path: str, event: Event) -> None:
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute(INSERT_EVENT, (
            event.user_id,
            event.title,
            event.start_at.isoformat(),
            event.end_at.isoformat(),
            event.description,
            event.location
        )
    )

    connection.commit()
    connection.close()


def list_events(database_path: str, user_id: int) -> list[Event]:
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute(LIST_EVENTS, (user_id,))
    rows_list = cursor.fetchall()
    event_list = []

    for row in rows_list:
        event = Event(
            id =                              row[0],
            user_id =                         row[1],
            title =                           row[2],
            start_at = datetime.fromisoformat(row[3]),
            end_at =   datetime.fromisoformat(row[4]),
            description =                     row[5],
            location =                        row[6],
        )

        event_list.append(event)

    connection.close()
    return event_list

def delete_event(database_path: str, user_id: int, event_id: int) -> bool:
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    cursor.execute(DELETE_EVENT, (event_id, user_id))
    deleted = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return deleted

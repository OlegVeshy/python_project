"""OpenAI-based parser that extracts calendar events from free-form text."""

import json
from datetime import datetime

from openai import OpenAI

from calendar_bot.events import ParsedEvent


DEFAULT_MODEL = "gpt-4.1-mini"


EVENT_SCHEMA = {
    "name": "parsed_event",
    "schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Short event title.",
            },
            "start_at": {
                "type": "string",
                "description": "Event start datetime in ISO 8601 format. For deadlines, this is the deadline moment.",
            },
            "end_at": {
                "type": "string",
                "description": "Event end datetime in ISO 8601 format. For instant events and deadlines, this must equal start_at.",
            },
            "description": {
                "type": ["string", "null"],
                "description": "Extra useful details from the message.",
            },
            "location": {
                "type": ["string", "null"],
                "description": "Event location if it is mentioned.",
            },
            "confidence": {
                "type": "number",
                "description": "Parsing confidence from 0 to 1.",
            },
        },
        "required": [
            "title",
            "start_at",
            "end_at",
            "description",
            "location",
            "confidence",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


def parse_event(
    text: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    now: datetime | None = None,
) -> ParsedEvent:
    """Parse one user message into a structured event draft."""

    if now is None:
        now = datetime.now()

    client = OpenAI(api_key=api_key)
    response_format = {
        "type": "json_schema",
        "json_schema": EVENT_SCHEMA,
    }

    response = client.chat.completions.create(
        model=model,
        response_format=response_format,  # type: ignore[arg-type]
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract calendar events from user messages. "
                    f"Current datetime is {now.isoformat()}. "
                    "Return only the structured data requested by the schema. "
                    "Distinguish scheduled events from instant events. "
                    "Scheduled events are meetings, classes, calls, visits, and other activities with duration. "
                    "Instant events are deadlines, reminders, tasks due at a certain time, or point-in-time notes. "
                    "For instant events, set end_at exactly equal to start_at. "
                    "For deadline phrases like 'до 18:00', 'deadline at 18:00', or 'сдать проект к пятнице', "
                    "use the due date and time as both start_at and end_at. "
                    "If a scheduled event does not mention duration, use 1 hour. "
                    "If the user does not mention a location, use null. "
                    "If the user does not mention a description, use null. "
                    "If the date or time is unclear, make the best reasonable "
                    "guess and lower confidence."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
    )

    content = response.choices[0].message.content
    if content is None:
        raise ValueError("OpenAI returned empty response")

    data = json.loads(content)

    return ParsedEvent(
        title=data["title"],
        start_at=datetime.fromisoformat(data["start_at"]),
        end_at=datetime.fromisoformat(data["end_at"]),
        description=data["description"],
        location=data["location"],
        confidence=data["confidence"],
    )

"""OpenAI-based parser that extracts calendar events from free-form text."""

import json
from datetime import datetime

from openai import OpenAI

from calendar_bot.events import ParsedEvent


DEFAULT_MODEL = "gpt-4o-mini"


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
                "description": "Event start datetime in ISO 8601 format.",
            },
            "end_at": {
                "type": "string",
                "description": "Event end datetime in ISO 8601 format.",
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
                    "If the user does not mention event duration, use 1 hour. "
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

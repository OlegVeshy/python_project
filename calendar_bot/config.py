"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from calendar_bot.exceptions import ConfigError


@dataclass(frozen=True)
class Config:
    """Runtime settings required to start the bot."""

    telegram_bot_token: str
    openai_api_key: str
    database_path: str


def load_config() -> Config:
    """Load required settings from `.env` and validate that they exist."""

    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_key = os.getenv("OPENAI_API_KEY")
    database_path = os.getenv("DATABASE_PATH")

    if token is None:
        raise ConfigError("Telegram bot token is not set")

    if api_key is None:
        raise ConfigError("OpenAI API key is not set")

    if database_path is None:
        raise ConfigError("Database path must be provided manually")

    return Config(
        telegram_bot_token=token,
        openai_api_key=api_key,
        database_path=database_path,
    )

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from calendar_bot.exceptions import ConfigError


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    openai_api_key: str
    database_path: str


def load_config() -> Config:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_key = os.getenv("OPENAI_API_KEY")
    database_path = os.getenv("DATABASE_PATH")

    if token is None:
        raise ConfigError("Telegram bot token is not set")

    if api_key is None:
        raise ConfigError("Openai API key is not set")
    
    if database_path is None:
        raise ConfigError("Database path must be provided manualy")

    return Config(
        telegram_bot_token=token,
        openai_api_key=api_key,
        database_path=database_path
    )


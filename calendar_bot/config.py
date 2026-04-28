import os
from dataclasses import dataclass

from dotenv import load_dotenv

from calendar_bot.exceptions import ConfigError


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    openai_api_key: str


def load_config() -> Config:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_key = os.getenv("OPENAI_API_KEY")

    if token is None:
        raise ConfigError("Telegram bot token is not set")

    if api_key is None:
        raise ConfigError("Openai API key is not set")

    return Config(
        telegram_bot_token=token,
        openai_api_key=api_key,
    )

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from calendar_bot.exceptions import ConfigError

@dataclass(frozen=True)
class Config:
    telegram_bot_token: str

def load_config() -> Config:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token is None:
        raise ConfigError("TELEGRAM_BOT_TOKEN is not set")
    return Config(telegram_bot_token=token)
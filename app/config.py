"""Конфигурация приложения через переменные окружения."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Загружаем переменные из .env (если файл есть рядом с запуском).
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Простые настройки проекта.

    Секреты не храним в коде: берем из окружения/.env.
    """

    db_path: str = os.getenv("DB_PATH", "./zen_ref_agent.db")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")


settings = Settings()

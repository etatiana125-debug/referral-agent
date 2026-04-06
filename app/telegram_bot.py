"""Отправка черновика в Telegram на ручную проверку."""

from __future__ import annotations


class TelegramSendError(RuntimeError):
    """Ошибка отправки сообщения в Telegram."""


def send_markdown_message(bot_token: str, chat_id: str, text: str) -> None:
    """Отправляет сообщение через Bot API.

    Для MVP используем обычный text без сложного форматирования,
    чтобы избежать проблем с экранированием Markdown.
    """
    if not bot_token or not chat_id:
        raise TelegramSendError("TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не настроены.")

    import requests

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }

    response = requests.post(url, json=payload, timeout=20)
    if response.status_code >= 400:
        raise TelegramSendError(f"Telegram API error {response.status_code}: {response.text}")

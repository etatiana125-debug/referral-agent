from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse


def build_utm_link(base_url: str, source: str, campaign: str) -> str:
    """Добавляет UTM-параметры к ссылке без потери существующих query-параметров."""
    parsed = urlparse(base_url)
    current_query = dict(parse_qsl(parsed.query))

    current_query.update(
        {
            "utm_source": source,
            "utm_medium": "social",
            "utm_campaign": campaign,
        }
    )

    new_query = urlencode(current_query)
    return urlunparse(parsed._replace(query=new_query))


def build_telegram_text(title: str, description: str, utm_link: str) -> str:
    """Формирует дружелюбный текст для Telegram-поста."""
    return (
        f"{title}\n\n"
        f"{description}\n\n"
        f"Если хотите разобрать тему глубже, вот полезная ссылка: {utm_link}\n"
        f"#полезное #обучение"
    )


def build_vk_text(title: str, description: str, utm_link: str) -> str:
    """Формирует дружелюбный текст для поста во ВКонтакте."""
    return (
        f"{title}\n\n"
        f"Коротко по сути: {description}\n\n"
        f"Подробнее и с примерами: {utm_link}\n"
        f"Подписывайтесь, если полезно 🙌"
    )

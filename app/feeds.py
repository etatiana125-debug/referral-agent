"""Загрузка новостей из RSS-лент."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_AI_FEEDS = [
    "https://openai.com/news/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.wired.com/feed/tag/ai/latest/rss",
]


@dataclass
class FeedItem:
    feed_url: str
    title: str
    link: str
    summary: str
    published_at: str | None = None


def fetch_feed_items(feed_urls: list[str] | None = None, max_per_feed: int = 10) -> list[FeedItem]:
    """Забирает элементы из RSS-лент.

    - Если лента недоступна/битая, просто пропускаем ее.
    - Если у записи нет ссылки, пропускаем запись.
    """
    import feedparser

    items: list[FeedItem] = []
    urls = feed_urls or DEFAULT_AI_FEEDS

    for feed_url in urls:
        parsed = feedparser.parse(feed_url)

        # bozo=True означает проблему парсинга/доступа.
        if getattr(parsed, "bozo", False):
            continue

        for entry in parsed.entries[:max_per_feed]:
            link = getattr(entry, "link", "")
            if not link:
                continue

            items.append(
                FeedItem(
                    feed_url=feed_url,
                    title=getattr(entry, "title", "Без названия"),
                    link=link,
                    summary=getattr(entry, "summary", ""),
                    published_at=getattr(entry, "published", None),
                )
            )

    return items

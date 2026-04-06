"""Оркестрация шагов MVP-пайплайна."""

from __future__ import annotations

from app.ai import generate_article_idea, generate_draft_article
from app.feeds import fetch_feed_items
from app.storage import Storage


def run_research(storage: Storage) -> dict[str, int]:
    """Шаг research: RSS -> source_items -> ideas."""
    source_saved = 0
    ideas_saved = 0
    duplicates = 0

    items = fetch_feed_items()

    for item in items:
        source_id = storage.insert_source_item(
            feed_url=item.feed_url,
            title=item.title,
            link=item.link,
            summary=item.summary,
            published_at=item.published_at,
        )

        # None здесь означает: дубль или пустая ссылка.
        if source_id is None:
            duplicates += 1
            continue

        source_saved += 1
        idea = generate_article_idea(
            source_item_id=source_id,
            source_title=item.title,
            source_summary=item.summary,
        )
        storage.insert_idea(idea)
        ideas_saved += 1

    return {
        "fetched": len(items),
        "source_saved": source_saved,
        "ideas_saved": ideas_saved,
        "duplicates": duplicates,
    }


def create_draft_for_idea(storage: Storage, idea_id: int) -> int:
    """Создает и сохраняет черновик по идее."""
    row = storage.get_idea(idea_id)
    if not row:
        raise ValueError(f"Идея с id={idea_id} не найдена")

    draft = generate_draft_article(
        idea_id=idea_id,
        idea_title=row["title"],
        angle=row["angle"],
        source_link=row["source_link"],
    )
    return storage.insert_draft(draft)

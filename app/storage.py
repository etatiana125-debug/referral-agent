"""Работа с SQLite: инициализация схемы и CRUD-операции."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from app.schemas import ArticleIdea, DraftArticle


class Storage:
    """Тонкая обертка над sqlite3 для MVP."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> bool:
        """Создает базовые таблицы, если их нет.

        Возвращает True, если файл БД создается впервые.
        """
        db_file = Path(self.db_path)
        first_run = not db_file.exists()
        db_file.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS source_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feed_url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    link TEXT UNIQUE,
                    summary TEXT,
                    published_at TEXT,
                    ingested_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ideas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_item_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    angle TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(source_item_id) REFERENCES source_items(id)
                );

                CREATE TABLE IF NOT EXISTS drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idea_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    body_markdown TEXT NOT NULL,
                    risk_level TEXT NOT NULL DEFAULT 'low',
                    disclaimer TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    sent_to_telegram_at TEXT,
                    FOREIGN KEY(idea_id) REFERENCES ideas(id)
                );
                """
            )

            # Миграция для БД, созданных до добавления risk_level в drafts.
            columns = conn.execute("PRAGMA table_info(drafts)").fetchall()
            column_names = [str(row[1]) for row in columns]
            if "risk_level" not in column_names:
                conn.execute("ALTER TABLE drafts ADD COLUMN risk_level TEXT NOT NULL DEFAULT 'low'")

        return first_run

    def insert_source_item(
        self,
        feed_url: str,
        title: str,
        link: str,
        summary: str,
        published_at: str | None,
    ) -> int | None:
        """Сохраняет новость. Если link уже есть — пропускает."""
        if not link:
            return None

        with self._connect() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO source_items (feed_url, title, link, summary, published_at, ingested_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feed_url,
                        title,
                        link,
                        summary,
                        published_at,
                        datetime.utcnow().isoformat(),
                    ),
                )
                return int(cursor.lastrowid)
            except sqlite3.IntegrityError:
                return None

    def list_recent_source_items(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, feed_url, title, link, summary, published_at, ingested_at
                FROM source_items
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def insert_idea(self, idea: ArticleIdea) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO ideas (source_item_id, title, angle, risk_level, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    idea.source_item_id,
                    idea.title,
                    idea.angle,
                    idea.risk_level,
                    idea.notes,
                    datetime.utcnow().isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def list_ideas(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT i.id, i.source_item_id, i.title, i.angle, i.risk_level, i.notes, i.created_at,
                       s.title AS source_title, s.link AS source_link
                FROM ideas i
                JOIN source_items s ON s.id = i.source_item_id
                ORDER BY i.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_idea(self, idea_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT i.id, i.source_item_id, i.title, i.angle, i.risk_level, i.notes, i.created_at,
                       s.title AS source_title, s.summary AS source_summary, s.link AS source_link
                FROM ideas i
                JOIN source_items s ON s.id = i.source_item_id
                WHERE i.id = ?
                """,
                (idea_id,),
            ).fetchone()
            return dict(row) if row else None

    def insert_draft(self, draft: DraftArticle) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO drafts (idea_id, title, body_markdown, risk_level, disclaimer, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    draft.idea_id,
                    draft.title,
                    draft.body_markdown,
                    draft.risk_level,
                    draft.disclaimer,
                    draft.created_at.isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def get_draft(self, draft_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT d.id, d.idea_id, d.title, d.body_markdown, d.risk_level, d.disclaimer,
                       d.created_at, d.sent_to_telegram_at
                FROM drafts d
                WHERE d.id = ?
                """,
                (draft_id,),
            ).fetchone()
            return dict(row) if row else None

    def mark_draft_sent(self, draft_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE drafts
                SET sent_to_telegram_at = ?
                WHERE id = ?
                """,
                (datetime.utcnow().isoformat(), draft_id),
            )

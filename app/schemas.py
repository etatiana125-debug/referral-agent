"""Pydantic-схемы для идей и черновиков."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ArticleIdea(BaseModel):
    """Идея статьи, полученная на основе новостей."""

    title: str = Field(..., description="Короткий заголовок идеи")
    angle: str = Field(..., description="Угол подачи/основной тезис")
    source_item_id: int = Field(..., ge=1)
    risk_level: str = Field(..., pattern="^(low|medium|high)$")
    notes: str = Field(default="", description="Комментарий по рискам/фактчекингу")


class DraftArticle(BaseModel):
    """Черновик статьи для ручной редакторской проверки."""

    idea_id: int = Field(..., ge=1)
    title: str
    body_markdown: str
    risk_level: str = Field(..., pattern="^(low|medium|high)$")
    disclaimer: str = "Черновик. Нужна ручная проверка перед публикацией."
    created_at: datetime = Field(default_factory=datetime.utcnow)

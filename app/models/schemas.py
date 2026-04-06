from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DraftCreateRequest(BaseModel):
    """Входные данные для генерации черновика из Pinterest-пина."""

    pin_title: str = Field(..., description="Заголовок пина")
    pin_description: str = Field(..., description="Описание пина")
    source_url: str = Field(..., description="Ссылка на исходный пин")
    referral_url: str = Field(..., description="Реферальная ссылка")
    campaign: str = Field(default="spring_campaign", description="Название UTM-кампании")


class DraftResponse(BaseModel):
    """Модель черновика, который хранится и отдается через API."""

    id: str
    status: Literal["draft", "approved", "rejected"] = "draft"
    created_at: datetime
    source_url: str
    telegram_text: str
    vk_text: str
    hooks: list[str] = Field(default_factory=list)
    cta_variants: list[str] = Field(default_factory=list)
    selected_hook: str | None = None
    selected_cta: str | None = None


class ApproveDraftResponse(BaseModel):
    """Ответ API после одобрения черновика."""

    draft_id: str
    status: Literal["approved"]
    message: str


class RejectDraftResponse(BaseModel):
    """Ответ API после отклонения черновика."""

    draft_id: str
    status: Literal["rejected"]
    message: str


class PinRecord(BaseModel):
    """Строка Pinterest-пина после импорта из CSV."""

    pin_id: str
    title: str
    description: str
    board: str
    keywords: str
    referral_link: str


class ImportPinsRequest(BaseModel):
    """Запрос на импорт CSV-файла через API."""

    csv_file_path: str = Field(
        default="data/pinterest_pins_example.csv",
        description="Путь к CSV-файлу для импорта",
    )


class ImportPinsResponse(BaseModel):
    """Результат импорта пинов."""

    imported_count: int
    output_file: str

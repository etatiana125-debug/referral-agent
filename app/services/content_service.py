from datetime import UTC, datetime
from uuid import uuid4

from app.models.schemas import DraftCreateRequest, DraftResponse
from app.services.storage_service import StorageService
from app.templates.message_templates import build_content_options, build_telegram_text, build_utm_link, build_vk_text


class ContentService:
    """Сервис с базовой логикой генерации и модерации черновиков."""

    def __init__(self, storage_service: StorageService) -> None:
        self.storage_service = storage_service

    def create_draft_from_pin(self, payload: DraftCreateRequest) -> DraftResponse:
        """Создает и сохраняет новый черновик на основе данных пина."""
        utm_link = build_utm_link(payload.referral_url, source="pinterest", campaign=payload.campaign)
        existing_drafts = self.storage_service.load_drafts()
        recent_hook = existing_drafts[-1].hooks[0] if existing_drafts and existing_drafts[-1].hooks else None
        recent_cta = existing_drafts[-1].cta_variants[0] if existing_drafts and existing_drafts[-1].cta_variants else None

        hooks, cta_variants = build_content_options(
            title=payload.pin_title,
            description=payload.pin_description,
            utm_link=utm_link,
            recent_hook=recent_hook,
            recent_cta=recent_cta,
        )

        telegram_text = build_telegram_text(
            title=payload.pin_title,
            description=payload.pin_description,
            hooks=hooks,
            cta=cta_variants[0],
        )
        vk_text = build_vk_text(
            title=payload.pin_title,
            description=payload.pin_description,
            hooks=hooks,
            cta=cta_variants[1],
        )

        draft = DraftResponse(
            id=str(uuid4()),
            status="draft",
            created_at=datetime.now(UTC),
            source_url=payload.source_url,
            telegram_text=telegram_text,
            vk_text=vk_text,
            hooks=hooks,
            cta_variants=cta_variants,
            selected_hook=None,
            selected_cta=None,
        )

        self.storage_service.save_draft(draft)
        return draft

    def list_drafts(self) -> list[DraftResponse]:
        """Возвращает все сохраненные черновики."""
        return self.storage_service.load_drafts()

    def get_draft(self, draft_id: str) -> DraftResponse | None:
        """Возвращает черновик по ID."""
        for draft in self.storage_service.load_drafts():
            if draft.id == draft_id:
                return draft
        return None

    def save_selected_options(self, draft_id: str, selected_hook: str, selected_cta: str) -> bool:
        """Сохраняет выбранные пользователем хук и CTA в черновике."""
        drafts = self.storage_service.load_drafts()

        for draft in drafts:
            if draft.id == draft_id:
                draft.selected_hook = selected_hook
                draft.selected_cta = selected_cta
                self.storage_service.overwrite_drafts(drafts)
                return True

        return False

    def approve_draft(self, draft_id: str) -> bool:
        """Обновляет статус черновика на approved."""
        return self._update_draft_status(draft_id=draft_id, new_status="approved")

    def reject_draft(self, draft_id: str) -> bool:
        """Обновляет статус черновика на rejected."""
        return self._update_draft_status(draft_id=draft_id, new_status="rejected")

    def _update_draft_status(self, draft_id: str, new_status: str) -> bool:
        drafts = self.storage_service.load_drafts()
        updated = False

        for draft in drafts:
            if draft.id == draft_id:
                draft.status = new_status
                updated = True
                break

        if updated:
            self.storage_service.overwrite_drafts(drafts)

        return updated

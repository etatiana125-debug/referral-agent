from app.models.schemas import DraftCreateRequest
from app.services.content_service import ContentService
from app.services.storage_service import StorageService


def test_approve_and_reject_draft(tmp_path) -> None:
    storage = StorageService(file_path=str(tmp_path / "drafts.json"))
    service = ContentService(storage_service=storage)

    draft = service.create_draft_from_pin(
        DraftCreateRequest(
            pin_title="Title",
            pin_description="Desc",
            source_url="https://example.com/pin/1",
            referral_url="https://example.com/ref/1",
            campaign="test",
        )
    )

    assert len(draft.hooks) == 3
    assert len(draft.cta_variants) == 2

    assert service.approve_draft(draft.id) is True
    assert service.list_drafts()[0].status == "approved"

    assert service.reject_draft(draft.id) is True
    assert service.list_drafts()[0].status == "rejected"

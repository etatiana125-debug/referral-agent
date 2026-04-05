from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.models.schemas import (
    ApproveDraftResponse,
    DraftCreateRequest,
    DraftResponse,
    ImportPinsRequest,
    ImportPinsResponse,
    PinRecord,
    RejectDraftResponse,
)
from app.services.content_service import ContentService
from app.services.pin_import_service import PinImportService
from app.services.storage_service import StorageService

app = FastAPI(title="Referral Content Agent", version="0.3.0")
templates = Jinja2Templates(directory="app/templates")

# Инициализируем сервисы один раз при запуске приложения.
storage_service = StorageService(file_path="data/drafts.json")
content_service = ContentService(storage_service=storage_service)
pin_import_service = PinImportService(output_file_path="data/pins.json")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/drafts/from-pin", response_model=DraftResponse)
def create_draft_from_pin(payload: DraftCreateRequest) -> DraftResponse:
    return content_service.create_draft_from_pin(payload)


@app.get("/drafts", response_model=list[DraftResponse])
def list_drafts() -> list[DraftResponse]:
    return content_service.list_drafts()


@app.post("/drafts/{draft_id}/approve", response_model=ApproveDraftResponse)
def approve_draft(draft_id: str) -> ApproveDraftResponse:
    approved = content_service.approve_draft(draft_id)
    if not approved:
        raise HTTPException(status_code=404, detail="Draft not found")

    return ApproveDraftResponse(
        draft_id=draft_id,
        status="approved",
        message="Черновик одобрен. Публикация пока не реализована.",
    )


@app.post("/drafts/{draft_id}/reject", response_model=RejectDraftResponse)
def reject_draft(draft_id: str) -> RejectDraftResponse:
    rejected = content_service.reject_draft(draft_id)
    if not rejected:
        raise HTTPException(status_code=404, detail="Draft not found")

    return RejectDraftResponse(
        draft_id=draft_id,
        status="rejected",
        message="Черновик отклонен.",
    )


@app.post("/imports/pins-csv", response_model=ImportPinsResponse)
def import_pins_from_csv(payload: ImportPinsRequest) -> ImportPinsResponse:
    try:
        imported_count = pin_import_service.import_from_csv(payload.csv_file_path)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return ImportPinsResponse(imported_count=imported_count, output_file="data/pins.json")


@app.get("/pins", response_model=list[PinRecord])
def list_imported_pins() -> list[PinRecord]:
    return pin_import_service.load_pins()


@app.get("/")
def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/web/pins")
def pins_page(request: Request, message: str = ""):
    pins = pin_import_service.load_pins()
    return templates.TemplateResponse(
        "pins.html",
        {
            "request": request,
            "pins": pins,
            "message": message,
        },
    )


@app.post("/web/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    uploads_dir = Path("data/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Сохраняем файл на диск, чтобы повторно использовать его при отладке.
    saved_path = uploads_dir / (file.filename or "pins.csv")
    contents = await file.read()
    saved_path.write_bytes(contents)

    try:
        imported_count = pin_import_service.import_from_csv(str(saved_path))
    except ValueError as error:
        return RedirectResponse(url=f"/web/pins?message={str(error)}", status_code=303)

    return RedirectResponse(
        url=f"/web/pins?message=Импортировано пинов: {imported_count}",
        status_code=303,
    )


@app.post("/web/pins/{pin_id}/generate")
def generate_draft_from_pin(pin_id: str):
    pin = pin_import_service.get_pin_by_id(pin_id)
    if not pin:
        return RedirectResponse(url="/web/pins?message=Пин не найден", status_code=303)

    payload = DraftCreateRequest(
        pin_title=pin.title,
        pin_description=pin.description,
        source_url=f"https://www.pinterest.com/pin/{pin.pin_id}/",
        referral_url=pin.referral_link,
        campaign="from_web_ui",
    )
    content_service.create_draft_from_pin(payload)

    return RedirectResponse(url="/web/drafts?message=Черновик создан", status_code=303)


@app.get("/web/drafts")
def drafts_page(request: Request, message: str = ""):
    drafts = content_service.list_drafts()
    return templates.TemplateResponse(
        "drafts.html",
        {
            "request": request,
            "drafts": drafts,
            "message": message,
        },
    )


@app.post("/web/drafts/{draft_id}/approve")
def approve_draft_from_ui(draft_id: str):
    if not content_service.approve_draft(draft_id):
        return RedirectResponse(url="/web/drafts?message=Черновик не найден", status_code=303)
    return RedirectResponse(url="/web/drafts?message=Черновик одобрен", status_code=303)


@app.post("/web/drafts/{draft_id}/reject")
def reject_draft_from_ui(draft_id: str):
    if not content_service.reject_draft(draft_id):
        return RedirectResponse(url="/web/drafts?message=Черновик не найден", status_code=303)
    return RedirectResponse(url="/web/drafts?message=Черновик отклонен", status_code=303)

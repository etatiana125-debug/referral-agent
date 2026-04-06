from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
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
from app.services.image_analysis_service import ImageAnalysisService
from app.services.image_import_service import ImageImportService
from app.services.pin_import_service import PinImportService
from app.services.storage_service import StorageService

app = FastAPI(title="Referral Content Agent", version="0.5.0")
templates = Jinja2Templates(directory="app/templates")

# Инициализируем сервисы один раз при запуске приложения.
storage_service = StorageService(file_path="data/drafts.json")
content_service = ContentService(storage_service=storage_service)
pin_import_service = PinImportService(output_file_path="data/pins.json")
image_analysis_service = ImageAnalysisService()
image_import_service = ImageImportService(image_analysis_service=image_analysis_service)


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

    saved_path = uploads_dir / (file.filename or "pins.csv")
    contents = await file.read()
    saved_path.write_bytes(contents)

    try:
        imported_count = pin_import_service.import_from_csv(str(saved_path))
    except ValueError as error:
        return RedirectResponse(url=f"/web/pins?message={str(error)}", status_code=303)

    return RedirectResponse(
        url=f"/web/pins?message=Импортировано пинов из CSV: {imported_count}",
        status_code=303,
    )


@app.post("/web/upload-images")
async def upload_images(
    image_files: list[UploadFile] = File(default=[]),
    zip_file: UploadFile | None = File(default=None),
    board: str = Form(default="Image Imports"),
    referral_link: str = Form(default="https://example.com/ref/default"),
):
    uploads_dir = Path("data/uploads/images") / datetime.now().strftime("%Y%m%d_%H%M%S")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    collected_image_paths: list[Path] = []

    # 1) Сохраняем загруженные изображения.
    for upload in image_files:
        if not upload.filename:
            continue
        file_path = uploads_dir / upload.filename
        file_path.write_bytes(await upload.read())
        collected_image_paths.append(file_path)

    # 2) Если есть ZIP — извлекаем изображения из архива.
    if zip_file and zip_file.filename:
        zip_path = uploads_dir / zip_file.filename
        zip_path.write_bytes(await zip_file.read())
        extracted_paths = image_import_service.extract_zip_images(
            zip_path=zip_path,
            output_dir=uploads_dir / "unzipped",
        )
        collected_image_paths.extend(extracted_paths)

    if not collected_image_paths:
        return RedirectResponse(url="/web/pins?message=Не найдено изображений для импорта", status_code=303)

    pins = image_import_service.build_pins_from_images(
        image_paths=collected_image_paths,
        board=board or "Image Imports",
        referral_link=referral_link or "https://example.com/ref/default",
    )

    if not pins:
        return RedirectResponse(url="/web/pins?message=Поддерживаются только JPG/JPEG/PNG", status_code=303)

    pin_import_service.save_pins(pins, mode="append")
    return RedirectResponse(
        url=f"/web/pins?message=Импортировано пинов из изображений: {len(pins)}",
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
        pin_id=pin.pin_id,
    )
    draft = content_service.create_draft_from_pin(payload)

    return RedirectResponse(url=f"/web/drafts/{draft.id}?message=Черновик создан", status_code=303)


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


@app.get("/web/drafts/{draft_id}")
def draft_detail_page(request: Request, draft_id: str, message: str = ""):
    draft = content_service.get_draft(draft_id)
    if not draft:
        return RedirectResponse(url="/web/drafts?message=Черновик не найден", status_code=303)

    return templates.TemplateResponse(
        "draft_detail.html",
        {
            "request": request,
            "draft": draft,
            "message": message,
        },
    )


@app.post("/web/drafts/{draft_id}/select-options")
def select_draft_options(draft_id: str, selected_hook: str = Form(...), selected_cta: str = Form(...)):
    updated = content_service.save_selected_options(
        draft_id=draft_id,
        selected_hook=selected_hook,
        selected_cta=selected_cta,
    )
    if not updated:
        return RedirectResponse(url="/web/drafts?message=Черновик не найден", status_code=303)

    return RedirectResponse(url=f"/web/drafts/{draft_id}?message=Выбор сохранен", status_code=303)


@app.post("/web/drafts/{draft_id}/approve")
def approve_draft_from_ui(draft_id: str):
    if not content_service.approve_draft(draft_id):
        return RedirectResponse(url="/web/drafts?message=Черновик не найден", status_code=303)
    return RedirectResponse(url=f"/web/drafts/{draft_id}?message=Черновик одобрен", status_code=303)


@app.post("/web/drafts/{draft_id}/reject")
def reject_draft_from_ui(draft_id: str):
    if not content_service.reject_draft(draft_id):
        return RedirectResponse(url="/web/drafts?message=Черновик не найден", status_code=303)
    return RedirectResponse(url=f"/web/drafts/{draft_id}?message=Черновик отклонен", status_code=303)

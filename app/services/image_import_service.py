from pathlib import Path
from uuid import uuid4
import zipfile

from app.models.schemas import PinRecord
from app.services.image_analysis_service import ImageAnalysisService


class ImageImportService:
    """Импортирует JPEG/PNG (или ZIP с ними) и создает заготовки пинов."""

    ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png"}

    def __init__(self, image_analysis_service: ImageAnalysisService) -> None:
        self.image_analysis_service = image_analysis_service

    def build_pins_from_images(
        self,
        image_paths: list[Path],
        board: str,
        referral_link: str,
    ) -> list[PinRecord]:
        pins: list[PinRecord] = []

        for image_path in image_paths:
            if image_path.suffix.lower() not in self.ALLOWED_SUFFIXES:
                continue

            analysis = self.image_analysis_service.analyze_image(image_path)
            pins.append(
                PinRecord(
                    pin_id=str(uuid4()),
                    title=analysis["title"],
                    description=analysis["description"],
                    board=board,
                    keywords=analysis["keywords"],
                    referral_link=referral_link,
                )
            )

        return pins

    def extract_zip_images(self, zip_path: Path, output_dir: Path) -> list[Path]:
        """Извлекает из ZIP только JPEG/PNG и возвращает пути к файлам."""
        output_dir.mkdir(parents=True, exist_ok=True)
        extracted_files: list[Path] = []

        with zipfile.ZipFile(zip_path, "r") as archive:
            for member in archive.infolist():
                member_path = Path(member.filename)
                if member.is_dir():
                    continue
                if member_path.suffix.lower() not in self.ALLOWED_SUFFIXES:
                    continue

                archive.extract(member, output_dir)
                extracted_files.append(output_dir / member.filename)

        return extracted_files

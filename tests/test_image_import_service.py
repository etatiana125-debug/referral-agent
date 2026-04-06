from pathlib import Path
import zipfile

from app.services.image_analysis_service import ImageAnalysisService
from app.services.image_import_service import ImageImportService


def test_build_pins_from_images(tmp_path: Path) -> None:
    image_path = tmp_path / "my_test_image.png"
    image_path.write_bytes(b"fake image")

    service = ImageImportService(image_analysis_service=ImageAnalysisService())
    pins = service.build_pins_from_images(
        image_paths=[image_path],
        board="Image Imports",
        referral_link="https://example.com/ref",
    )

    assert len(pins) == 1
    assert pins[0].title == "My Test: практичная идея"
    assert "my_test_image" not in pins[0].description.lower()
    assert "контент" in pins[0].keywords


def test_build_pins_from_technical_image(tmp_path: Path) -> None:
    image_path = tmp_path / "qr_20250101_abcd1234efgh5678.png"
    image_path.write_bytes(b"fake image")

    service = ImageImportService(image_analysis_service=ImageAnalysisService())
    pins = service.build_pins_from_images(
        image_paths=[image_path],
        board="Image Imports",
        referral_link="https://example.com/ref",
    )

    assert len(pins) == 1
    assert pins[0].title == "Техническое изображение"
    assert "служебный визуал" in pins[0].description.lower()


def test_extract_zip_images(tmp_path: Path) -> None:
    zip_path = tmp_path / "images.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("a.jpg", b"jpg")
        archive.writestr("b.png", b"png")
        archive.writestr("c.txt", b"skip")

    service = ImageImportService(image_analysis_service=ImageAnalysisService())
    extracted = service.extract_zip_images(zip_path=zip_path, output_dir=tmp_path / "out")

    names = sorted(path.name for path in extracted)
    assert names == ["a.jpg", "b.png"]

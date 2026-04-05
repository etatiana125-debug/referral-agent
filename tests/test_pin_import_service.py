from pathlib import Path

from app.services.pin_import_service import PinImportService


def test_import_from_csv_to_json(tmp_path: Path) -> None:
    csv_file = tmp_path / "pins.csv"
    output_json = tmp_path / "pins.json"

    csv_file.write_text(
        "pin_id,title,description,board,keywords,referral_link\n"
        "1,Title A,Description A,Board A,keyword1,https://example.com/ref/a\n",
        encoding="utf-8",
    )

    service = PinImportService(output_file_path=str(output_json))
    imported_count = service.import_from_csv(str(csv_file))

    assert imported_count == 1
    pins = service.load_pins()
    assert len(pins) == 1
    assert pins[0].pin_id == "1"
    assert pins[0].title == "Title A"

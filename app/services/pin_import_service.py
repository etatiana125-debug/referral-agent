import csv
import json
from pathlib import Path

from app.models.schemas import PinRecord


class PinImportService:
    """Сервис для импорта Pinterest-пинов из CSV и других источников в JSON."""

    REQUIRED_FIELDS = ["pin_id", "title", "description", "board", "keywords", "referral_link"]

    def __init__(self, output_file_path: str = "data/pins.json") -> None:
        self.output_file_path = Path(output_file_path)
        self.output_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Подготавливаем пустой JSON-файл, чтобы импорт работал "из коробки".
        if not self.output_file_path.exists():
            self.output_file_path.write_text("[]", encoding="utf-8")

    def import_from_csv(self, csv_file_path: str) -> int:
        """Импортирует пины из CSV и полностью обновляет JSON-файл."""
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

        with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            self._validate_headers(reader.fieldnames)

            pins: list[PinRecord] = []
            for row in reader:
                cleaned = {key: (value or "").strip() for key, value in row.items()}
                pins.append(PinRecord.model_validate(cleaned))

        self.save_pins(pins, mode="replace")
        return len(pins)

    def save_pins(self, pins: list[PinRecord], mode: str = "append") -> int:
        """Сохраняет пины в JSON.

        mode=append: добавляет к существующим.
        mode=replace: полностью заменяет файл.
        """
        existing = [] if mode == "replace" else self.load_pins()
        updated = existing + pins

        serializable = [pin.model_dump() for pin in updated]
        self.output_file_path.write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return len(pins)

    def load_pins(self) -> list[PinRecord]:
        """Возвращает все импортированные пины из JSON-файла."""
        raw = self.output_file_path.read_text(encoding="utf-8")
        items = json.loads(raw)
        return [PinRecord.model_validate(item) for item in items]

    def get_pin_by_id(self, pin_id: str) -> PinRecord | None:
        """Ищет пин по pin_id в уже импортированных данных."""
        for pin in self.load_pins():
            if pin.pin_id == pin_id:
                return pin
        return None

    def _validate_headers(self, fieldnames: list[str] | None) -> None:
        headers = fieldnames or []
        missing = [field for field in self.REQUIRED_FIELDS if field not in headers]
        if missing:
            raise ValueError(f"Missing required CSV columns: {', '.join(missing)}")

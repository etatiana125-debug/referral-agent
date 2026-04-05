import json
from pathlib import Path

from app.models.schemas import DraftResponse


class StorageService:
    """Простое файловое хранилище черновиков в JSON."""

    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Создаем файл при первом запуске, чтобы новичку было проще стартовать.
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def load_drafts(self) -> list[DraftResponse]:
        """Читает черновики из файла и возвращает как список моделей."""
        raw_data = self.file_path.read_text(encoding="utf-8")
        items = json.loads(raw_data)
        return [DraftResponse.model_validate(item) for item in items]

    def save_draft(self, draft: DraftResponse) -> None:
        """Добавляет новый черновик в файл."""
        drafts = self.load_drafts()
        drafts.append(draft)
        self.overwrite_drafts(drafts)

    def overwrite_drafts(self, drafts: list[DraftResponse]) -> None:
        """Полностью перезаписывает файл текущим списком черновиков."""
        serializable = [item.model_dump(mode="json") for item in drafts]
        self.file_path.write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

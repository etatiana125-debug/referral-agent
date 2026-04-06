from pathlib import Path


class ImageAnalysisService:
    """Сервис анализа изображения.

    Сейчас работает в безопасном fallback-режиме без vision-модели:
    - title строится из имени файла
    - description и keywords — по шаблону

    Позже можно заменить метод analyze_image на вызов реальной vision-модели.
    """

    def analyze_image(self, image_path: Path) -> dict[str, str]:
        file_stem = image_path.stem.replace("_", " ").replace("-", " ").strip()
        normalized_title = file_stem.title() if file_stem else "Новый визуал"

        return {
            "title": normalized_title,
            "description": f"Идея для поста на основе изображения: {normalized_title}.",
            "keywords": "контент, визуал, pinterest, идеи",
        }

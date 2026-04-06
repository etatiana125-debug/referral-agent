from pathlib import Path
import re


class ImageAnalysisService:
    """Сервис анализа изображения.

    Сейчас работает в безопасном fallback-режиме без vision-модели:
    - title строится из имени файла
    - description и keywords - по шаблону

    Позже можно заменить метод analyze_image на вызов реальной vision-модели.
    """

    TECHNICAL_MARKERS = {
        "qr",
        "qrcode",
        "barcode",
        "scan",
        "screenshot",
        "icon",
        "logo",
        "sprite",
        "thumb",
        "thumbnail",
        "tmp",
        "temp",
    }

    def analyze_image(self, image_path: Path) -> dict[str, str]:
        raw_name = image_path.stem
        topic = self._extract_topic(raw_name)
        technical = self._is_technical_image(raw_name=raw_name, topic=topic)

        if technical:
            return {
                "title": "Техническое изображение",
                "description": (
                    "Служебный визуал (например QR-код, скриншот или элемент интерфейса). "
                    "Рекомендуется ручная проверка перед публикацией."
                ),
                "keywords": "технический визуал, проверка, pinterest",
            }

        title = self._build_title(topic)
        description = self._build_description(topic)
        keywords = self._build_keywords(topic)

        return {"title": title, "description": description, "keywords": keywords}

    def _extract_topic(self, raw_name: str) -> str:
        cleaned = raw_name.lower()
        cleaned = cleaned.replace("_", " ").replace("-", " ").replace(".", " ")
        cleaned = re.sub(r"\b\d{4,}\b", " ", cleaned)
        cleaned = re.sub(r"\b[a-f0-9]{8,}\b", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        stopwords = {
            "img",
            "image",
            "photo",
            "pic",
            "final",
            "copy",
            "edited",
            "new",
            "v2",
            "v3",
            "draft",
            "file",
        }

        meaningful_tokens: list[str] = []
        for token in cleaned.split():
            if token in stopwords:
                continue
            if len(token) <= 1:
                continue
            if token.isdigit():
                continue
            meaningful_tokens.append(token)

        return " ".join(meaningful_tokens[:4]).strip()

    def _is_technical_image(self, raw_name: str, topic: str) -> bool:
        text = f"{raw_name} {topic}".lower()
        return any(marker in text for marker in self.TECHNICAL_MARKERS)

    def _build_title(self, topic: str) -> str:
        if not topic:
            return "Идея для нового поста"

        human_topic = " ".join(topic.split()[:3]).strip().title()
        return f"{human_topic}: практичная идея"

    def _build_description(self, topic: str) -> str:
        if not topic:
            return (
                "Подборка визуальной идеи для полезного поста: коротко, понятно и без лишних обещаний. "
                "Можно использовать как основу для Telegram и VK."
            )

        return (
            f"Идея на тему «{topic}»: покажите суть в 2-3 шагах, добавьте пример применения "
            "и завершите мягким CTA с полезной ссылкой."
        )

    def _build_keywords(self, topic: str) -> str:
        base_keywords = ["контент", "pinterest", "идеи", "полезный пост"]
        if topic:
            topic_keywords = [token for token in topic.split() if len(token) > 2][:3]
            base_keywords = topic_keywords + base_keywords
        return ", ".join(dict.fromkeys(base_keywords))

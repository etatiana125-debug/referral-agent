from functools import lru_cache
from hashlib import md5
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

PROMPTS_DIR = Path("prompts")

TG_OPENERS = [
    "Смотри, что нашла по этой теме.",
    "Вот что заметила, пока разбирала этот пин.",
    "В этой теме есть маленькая фишка, которая реально упрощает процесс.",
]

TG_ENDINGS = [
    "Если полезно, продолжу в таком формате 💛",
    "Если хотите, соберу ещё похожие идеи в отдельную подборку.",
    "Если тема откликнулась, в следующем посте разберу практические примеры.",
]

VK_INTROS = [
    "Если вам нужен понятный способ без лишней теории, вот суть в двух словах.",
    "Этот подход удобен тем, что его можно применить сразу, без сложного входа.",
    "Сохраняйте пост: здесь короткий и практичный разбор по теме.",
]

VK_ENDINGS = [
    "Если пост полезен, сохраните его и вернитесь к шагам позже.",
    "Если хотите, могу сделать продолжение с примерами под разные задачи.",
    "Напишите, если нужен разбор похожего кейса — подготовлю следующий пост.",
]


@lru_cache(maxsize=1)
def _load_style_context() -> dict[str, str]:
    """Читает стилевые файлы из prompts/ и возвращает их содержимое."""
    return {
        "shared_rules": (PROMPTS_DIR / "shared_rules.txt").read_text(encoding="utf-8"),
        "telegram_style": (PROMPTS_DIR / "telegram_style.txt").read_text(encoding="utf-8"),
        "vk_style": (PROMPTS_DIR / "vk_style.txt").read_text(encoding="utf-8"),
        "author_voice": (PROMPTS_DIR / "author_voice.txt").read_text(encoding="utf-8"),
    }


@lru_cache(maxsize=1)
def _load_hooks_library() -> list[str]:
    return _load_numbered_library(PROMPTS_DIR / "hooks_library.txt")


@lru_cache(maxsize=1)
def _load_cta_library() -> list[str]:
    return _load_numbered_library(PROMPTS_DIR / "cta_library.txt")


def build_utm_link(base_url: str, source: str, campaign: str) -> str:
    """Добавляет UTM-параметры к ссылке без потери существующих query-параметров."""
    parsed = urlparse(base_url)
    current_query = dict(parse_qsl(parsed.query))

    current_query.update(
        {
            "utm_source": source,
            "utm_medium": "social",
            "utm_campaign": campaign,
        }
    )

    new_query = urlencode(current_query)
    return urlunparse(parsed._replace(query=new_query))


def build_content_options(
    title: str,
    description: str,
    utm_link: str,
    recent_hook: str | None = None,
    recent_cta: str | None = None,
) -> tuple[list[str], list[str]]:
    """Генерирует 3 разных хука и 2 CTA-варианта с реферальной ссылкой."""
    _ = _load_style_context()  # Важно: генерация опирается на внешние стилевые файлы.
    hooks_library = _load_hooks_library()
    cta_library = _load_cta_library()

    seed = _seed_value(title=title, description=description)

    hooks = _pick_with_anti_repeat(
        templates=hooks_library,
        count=3,
        seed=seed,
        recent_value=recent_hook,
    )
    ctas = _pick_with_anti_repeat(
        templates=cta_library,
        count=2,
        seed=seed + 13,
        recent_value=recent_cta,
    )

    cta_with_link = [f"{cta} {utm_link}" for cta in ctas]
    return hooks, cta_with_link


def build_telegram_text(title: str, description: str, hooks: list[str], cta: str) -> str:
    """Telegram: более живой, тёплый и разговорный текст."""
    style = _load_style_context()
    seed = _seed_value(title=title, description=description)

    opener = _pick_unique_templates(TG_OPENERS, count=1, seed=seed + 5)[0]
    ending = _pick_unique_templates(TG_ENDINGS, count=1, seed=seed + 7)[0]

    topical_line = _topic_line(title=title, description=description)

    text = (
        f"{hooks[0]}\n\n"
        f"{opener}\n"
        f"{topical_line}\n"
        f"{description}\n\n"
        f"{cta}\n"
        f"{ending}"
    )
    return _polish_text(text, style)


def build_vk_text(title: str, description: str, hooks: list[str], cta: str) -> str:
    """VK: более структурный и понятный текст для ленты."""
    style = _load_style_context()
    seed = _seed_value(title=title, description=description)

    intro = _pick_unique_templates(VK_INTROS, count=1, seed=seed + 3)[0]
    ending = _pick_unique_templates(VK_ENDINGS, count=1, seed=seed + 9)[0]

    text = (
        f"{hooks[1]}\n\n"
        f"{intro}\n\n"
        f"Что это: {title}.\n"
        f"Зачем это полезно: {description}\n"
        f"Как применить: начните с одного шага и адаптируйте под свой формат.\n"
        f"Подробнее: {cta}\n\n"
        f"{ending}"
    )
    return _polish_text(text, style)


def _load_numbered_library(file_path: Path) -> list[str]:
    """Читает txt-библиотеку вида '1. ...' и возвращает список фраз."""
    lines = file_path.read_text(encoding="utf-8").splitlines()
    items: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("Варианты"):
            continue
        if ". " in stripped and stripped.split(". ", 1)[0].isdigit():
            items.append(stripped.split(". ", 1)[1])
    return items


def _pick_with_anti_repeat(
    templates: list[str],
    count: int,
    seed: int,
    recent_value: str | None,
) -> list[str]:
    picked = _pick_unique_templates(templates, count=count, seed=seed)
    if recent_value and picked and picked[0] == recent_value:
        picked = _pick_unique_templates(templates, count=count, seed=seed + 1)
    return picked


def _topic_line(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    keywords = ["ai", "визуал", "генерац", "pinterest", "контент", "маркет", "фото", "видео"]
    if any(word in text for word in keywords):
        return "Эта тема особенно полезна тем, кто работает с контентом, визуалом и идеями для ленты."
    return "Подход легко адаптируется под повседневные рабочие задачи."


def _polish_text(text: str, style_context: dict[str, str]) -> str:
    """Простая пост-обработка: чистим запрещённые обещания и делаем текст более аккуратным."""
    banned_phrases = [
        "заработай легко",
        "идеальное решение",
        "революционный инструмент",
        "быстрый заработок",
        "лёгкие деньги",
        "мгновенный успех",
    ]

    cleaned = text
    for phrase in banned_phrases:
        cleaned = cleaned.replace(phrase, "")
        cleaned = cleaned.replace(phrase.capitalize(), "")

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    deduplicated: list[str] = []
    for line in lines:
        if not deduplicated or deduplicated[-1] != line:
            deduplicated.append(line)

    _ = style_context["shared_rules"], style_context["telegram_style"], style_context["vk_style"], style_context["author_voice"]
    return "\n\n".join(deduplicated)


def _seed_value(title: str, description: str) -> int:
    raw = f"{title}|{description}".encode("utf-8")
    return int(md5(raw).hexdigest(), 16)


def _pick_unique_templates(templates: list[str], count: int, seed: int) -> list[str]:
    if count >= len(templates):
        return templates[:count]

    start = seed % len(templates)
    ordered = templates[start:] + templates[:start]
    return ordered[:count]

from functools import lru_cache
from hashlib import md5
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

PROMPTS_DIR = Path("app/prompts")


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


def build_content_options(title: str, description: str, utm_link: str) -> tuple[list[str], list[str]]:
    """Генерирует 3 разных хука и 2 CTA-варианта с учетом правил из текстовых файлов."""
    shared = _load_prompt_sections(PROMPTS_DIR / "shared_rules.txt")

    seed = _seed_value(title=title, description=description)
    hooks = _pick_unique_templates(shared["HOOKS"], count=3, seed=seed)
    ctas = _pick_unique_templates(shared["CTA"], count=2, seed=seed + 13)

    context = {
        "title": title,
        "title_lower": title.lower(),
        "description": description,
        "utm_link": utm_link,
    }

    banned = shared.get("BANNED_PHRASES", [])
    hook_texts = [_clean_style(template.format(**context), banned) for template in hooks]
    cta_texts = [_clean_style(template.format(**context), banned) for template in ctas]
    return hook_texts, cta_texts


def build_telegram_text(title: str, description: str, hooks: list[str], cta: str) -> str:
    """Telegram: более личный, теплый и разговорный стиль."""
    tg = _load_prompt_sections(PROMPTS_DIR / "telegram_style.txt")
    shared = _load_prompt_sections(PROMPTS_DIR / "shared_rules.txt")

    seed = _seed_value(title=title, description=description)
    body_template = _pick_unique_templates(tg["BODY"], count=1, seed=seed + 5)[0]
    ending = _pick_unique_templates(tg["ENDING"], count=1, seed=seed + 9)[0]

    body = body_template.format(title=title, title_lower=title.lower(), description=description)
    text = f"{hooks[0]}\n\n{body}\n\n{cta}\n{ending}"
    return _clean_style(text, shared.get("BANNED_PHRASES", []))


def build_vk_text(title: str, description: str, hooks: list[str], cta: str) -> str:
    """VK: более структурный стиль с вовлекающим первым абзацем."""
    vk = _load_prompt_sections(PROMPTS_DIR / "vk_style.txt")
    shared = _load_prompt_sections(PROMPTS_DIR / "shared_rules.txt")

    seed = _seed_value(title=title, description=description)
    intro = _pick_unique_templates(vk["INTRO"], count=1, seed=seed + 2)[0]
    ending = _pick_unique_templates(vk["ENDING"], count=1, seed=seed + 17)[0]

    text = (
        f"{hooks[1]}\n\n"
        f"{intro}\n"
        f"1) Что важно: {title}.\n"
        f"2) Коротко по сути: {description}\n"
        f"3) Что сделать дальше: {cta}\n\n"
        f"{ending}"
    )
    return _clean_style(text, shared.get("BANNED_PHRASES", []))


@lru_cache(maxsize=8)
def _load_prompt_sections(file_path: Path) -> dict[str, list[str]]:
    """Читает txt-файл со стилем и разбивает его на секции вида [SECTION]."""
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")

    sections: dict[str, list[str]] = {}
    current_section = ""

    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            sections.setdefault(current_section, [])
            continue

        if current_section:
            sections[current_section].append(line)

    return sections


def _clean_style(text: str, banned_phrases: list[str]) -> str:
    """Убирает запрещенные формулировки и лишние пробелы."""
    cleaned = text
    for phrase in banned_phrases:
        cleaned = cleaned.replace(phrase, "")
        cleaned = cleaned.replace(phrase.capitalize(), "")
    return " ".join(cleaned.split()) if "\n" not in cleaned else "\n".join(part.strip() for part in cleaned.splitlines())


def _seed_value(title: str, description: str) -> int:
    raw = f"{title}|{description}".encode("utf-8")
    return int(md5(raw).hexdigest(), 16)


def _pick_unique_templates(templates: list[str], count: int, seed: int) -> list[str]:
    if not templates:
        return []
    if count >= len(templates):
        return templates[:]

    start = seed % len(templates)
    ordered = templates[start:] + templates[:start]
    return ordered[:count]

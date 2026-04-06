"""Логика генерации идей/черновиков и простой риск-классификатор."""

from __future__ import annotations

from textwrap import dedent

from app.config import settings
from app.schemas import ArticleIdea, DraftArticle


def classify_risk(text: str) -> tuple[str, str]:
    """Классификатор promo/legal риска для редакторского процесса.

    low: нейтрально-редакционный, полезный материал.
    medium: есть упоминания платформ/сервисов.
    high: явный промо-пуш или прямые продажи.
    """
    t = text.lower()

    high_markers = [
        "купи",
        "покупайте",
        "жми ссылку",
        "успей купить",
        "только сегодня",
        "гарантированный доход",
        "заработаешь",
        "продаю",
        "оформляй подписку сейчас",
    ]
    medium_markers = [
        "платформа",
        "сервис",
        "инструмент",
        "подписка",
        "тариф",
        "рефераль",
        "партнерск",
    ]

    if any(marker in t for marker in high_markers):
        return "high", "Есть признаки агрессивного промо или прямого sales-push."

    if any(marker in t for marker in medium_markers):
        return "medium", "Есть упоминания платформ/сервисов — нужен аккуратный редакторский контроль."

    return "low", "Редакционно-полезная подача без явного промо."


def _generate_with_openai(system_prompt: str, user_prompt: str) -> str:
    """Мини-обертка вокруг OpenAI Responses API."""
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
    )
    return response.output_text.strip()


def _fallback_idea(source_title: str) -> tuple[str, str]:
    title = f"Что важно знать про: {source_title[:90]}"
    angle = "Спокойно разобрать новость, объяснить пользу и ограничения без рекламного давления."
    return title, angle


def generate_article_idea(source_item_id: int, source_title: str, source_summary: str) -> ArticleIdea:
    """Генерирует идею статьи по новости через OpenAI (или fallback)."""
    risk_level, notes = classify_risk(f"{source_title}\n{source_summary}")

    system_prompt = dedent(
        """
        Ты редактор русскоязычного Дзен-блога про AI.
        Подготовь идею спокойно, полезно, без кликбейта.
        Нельзя использовать агрессивные продажи и обещания дохода.
        """
    ).strip()

    user_prompt = dedent(
        f"""
        Источник:
        Заголовок: {source_title}
        Кратко: {source_summary}

        Верни:
        1) Короткий заголовок идеи.
        2) Угол подачи (1-2 предложения).
        """
    ).strip()

    if not settings.openai_api_key:
        title, angle = _fallback_idea(source_title)
        notes = f"{notes} OpenAI API key не задан, использован fallback."
    else:
        try:
            raw = _generate_with_openai(system_prompt, user_prompt)
            lines = [line.strip("-• ") for line in raw.splitlines() if line.strip()]
            title = lines[0] if lines else f"Идея по теме: {source_title[:80]}"
            angle = lines[1] if len(lines) > 1 else "Разобрать новость простым языком и показать практическую пользу."
        except Exception as exc:
            title, angle = _fallback_idea(source_title)
            notes = f"{notes} OpenAI недоступен ({exc.__class__.__name__}), использован fallback."

    return ArticleIdea(
        title=title,
        angle=angle,
        source_item_id=source_item_id,
        risk_level=risk_level,
        notes=notes,
    )


def _soft_cta_block() -> str:
    return dedent(
        """
        ## Мягкий CTA
        Если тема откликается, можно сохранить статью и спокойно протестировать один из инструментов на небольшой задаче.
        Без спешки: сначала проверка фактов, затем личный вывод, подходит ли это именно вам.
        """
    ).strip()


def generate_draft_article(idea_id: int, idea_title: str, angle: str, source_link: str) -> DraftArticle:
    """Генерирует черновик статьи в Zen-стиле на русском."""
    system_prompt = dedent(
        """
        Ты автор русскоязычных образовательных статей для Дзена про AI.
        Стиль: живой, современный, без канцелярита и спама.
        Обязательно:
        - мягкий CTA без давления;
        - не обещать доход и результат;
        - не использовать агрессивные продажи.
        """
    ).strip()

    user_prompt = dedent(
        f"""
        Подготовь черновик статьи для Дзена.

        Идея: {idea_title}
        Угол подачи: {angle}
        Ссылка на источник: {source_link}

        Формат:
        - Короткое вступление
        - 3-5 подзаголовков
        - Практические выводы
        - Блок с мягким CTA
        - Блок "Что проверить перед публикацией"
        """
    ).strip()

    body = ""
    if settings.openai_api_key:
        try:
            body = _generate_with_openai(system_prompt, user_prompt)
        except Exception:
            body = ""

    if not body:
        body = dedent(
            f"""
            # {idea_title}

            > Источник: {source_link}

            Вокруг AI много громких заявлений. В этой заметке — спокойный разбор без обещаний и без рекламного давления.

            ## Что произошло
            Кратко перескажем новость и отделим факт от интерпретации.

            ## Почему это может быть полезно
            Разберем, в каких задачах подход действительно может помочь, а где пока рано делать выводы.

            ## Ограничения и риски
            Укажем, что стоит перепроверить: источники, формулировки и контекст применения.

            ## Как применить идею аккуратно
            1. Начать с маленького сценария.
            2. Сравнить результат с привычным подходом.
            3. Зафиксировать плюсы и минусы до масштабирования.

            {_soft_cta_block()}

            ## Что проверить перед публикацией
            - Фактическую точность и даты.
            - Отсутствие чрезмерных обещаний.
            - Корректность упоминаний сервисов и платформ.
            """
        ).strip()

    draft_risk_level, _ = classify_risk(f"{idea_title}\n{body}")

    return DraftArticle(
        idea_id=idea_id,
        title=idea_title,
        body_markdown=body,
        risk_level=draft_risk_level,
    )

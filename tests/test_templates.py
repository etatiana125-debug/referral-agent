from app.templates.message_templates import build_content_options, build_telegram_text, build_utm_link, build_vk_text


def test_build_utm_link_adds_tags() -> None:
    result = build_utm_link("https://example.com/product", source="pinterest", campaign="test_campaign")

    assert "utm_source=pinterest" in result
    assert "utm_medium=social" in result
    assert "utm_campaign=test_campaign" in result


def test_build_content_options_count() -> None:
    hooks, ctas = build_content_options(
        title="Как быстрее учиться",
        description="Короткий метод из 3 шагов",
        utm_link="https://example.com/ref",
    )

    assert len(hooks) == 3
    assert len(ctas) == 2
    assert len(set(hooks)) == 3
    assert len(set(ctas)) == 2
    assert "https://example.com/ref" in ctas[0]


def test_platform_text_styles_are_different() -> None:
    hooks, ctas = build_content_options(
        title="Планирование контента",
        description="Простая структура, чтобы не выгорать",
        utm_link="https://example.com/ref",
    )

    tg_text = build_telegram_text(
        title="Планирование контента",
        description="Простая структура, чтобы не выгорать",
        hooks=hooks,
        cta=ctas[0],
    )
    vk_text = build_vk_text(
        title="Планирование контента",
        description="Простая структура, чтобы не выгорать",
        hooks=hooks,
        cta=ctas[1],
    )

    assert tg_text != vk_text
    assert "1) Что важно" in vk_text


def test_anti_repeat_for_recent_hook_and_cta() -> None:
    hooks, ctas = build_content_options(
        title="AI-контент",
        description="Идея для быстрых визуалов",
        utm_link="https://example.com/ref",
    )

    next_hooks, next_ctas = build_content_options(
        title="AI-контент",
        description="Идея для быстрых визуалов",
        utm_link="https://example.com/ref",
        recent_hook=hooks[0],
        recent_cta=ctas[0],
    )

    assert next_hooks[0] != hooks[0]
    assert next_ctas[0] != ctas[0]

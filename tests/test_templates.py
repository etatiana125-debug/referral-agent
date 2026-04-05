from app.templates.message_templates import build_utm_link


def test_build_utm_link_adds_tags() -> None:
    result = build_utm_link("https://example.com/product", source="pinterest", campaign="test_campaign")

    assert "utm_source=pinterest" in result
    assert "utm_medium=social" in result
    assert "utm_campaign=test_campaign" in result

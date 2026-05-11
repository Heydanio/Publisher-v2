"""Tests safeguards anti-spam."""
from src.core.safeguards import validate_tags, validate_title, sanitize_content


def test_validate_tags_valid():
    valid, _ = validate_tags(["#fun", "#video"], "youtube")
    assert valid is True


def test_validate_tags_too_many():
    tags = [f"#tag{i}" for i in range(20)]
    valid, _ = validate_tags(tags, "tiktok")
    assert valid is False


def test_validate_tags_spam():
    valid, _ = validate_tags(["#follow4follow"], "youtube")
    assert valid is False


def test_validate_title_short():
    valid, _ = validate_title("ab", "youtube")
    assert valid is False


def test_validate_title_caps():
    valid, _ = validate_title("THIS IS ALL UPPERCASE TITLE", "youtube")
    assert valid is False


def test_sanitize_content():
    text = "Hello\u200B World"  # Zero-width space
    cleaned = sanitize_content(text)
    assert "\u200B" not in cleaned

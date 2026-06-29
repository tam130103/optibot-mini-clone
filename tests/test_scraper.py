"""Tests for Zendesk scraper module."""

from src.scraper import slugify


def test_slugify_basic():
    assert slugify("How to Add a YouTube Video") == "how-to-add-a-youtube-video"


def test_slugify_special_chars():
    result = slugify("OptiSigns — Setup & Config (v2.0)")
    assert "optisigns" in result
    assert "&" not in result
    assert "(" not in result


def test_slugify_truncates():
    long_title = "A" * 200
    result = slugify(long_title)
    assert len(result) <= 80


def test_slugify_strips_edges():
    assert slugify("  Hello World  ") == "hello-world"

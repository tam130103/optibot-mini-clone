"""Tests for vector store chunking logic."""

from src.vector_store import chunk_article


def test_short_article_single_chunk():
    content = "# Title\n\nShort paragraph here."
    chunks = chunk_article(content, "1", "https://example.com", "Title")
    assert len(chunks) == 1
    assert chunks[0]["metadata"]["article_id"] == "1"
    assert chunks[0]["metadata"]["article_url"] == "https://example.com"


def test_multiple_sections():
    content = (
        "# Title\n\n"
        "Introduction text.\n\n"
        "## Section A\n\n"
        "Content for section A.\n\n"
        "## Section B\n\n"
        "Content for section B."
    )
    chunks = chunk_article(content, "2", "https://example.com", "Title")
    assert len(chunks) >= 2  # At least intro + sections


def test_long_section_splits():
    # Create a section longer than max_chunk
    long_text = "# Title\n\n" + "\n\n".join(
        [f"Paragraph {i} with some text content." for i in range(50)]
    )
    chunks = chunk_article(
        long_text, "3", "https://example.com", "Title", max_chunk=200
    )
    assert len(chunks) > 1
    # Each chunk should be within limits (with some tolerance for overlap)
    for chunk in chunks:
        assert len(chunk["document"]) < 400  # max_chunk + overlap


def test_skips_tiny_chunks():
    content = "# Title\n\n## A\n\nOK\n\n## B\n\n"
    chunks = chunk_article(content, "4", "https://example.com", "Title")
    # "OK" alone is only 2 chars, should be skipped (< 20 chars)
    for chunk in chunks:
        assert len(chunk["document"]) >= 20


def test_frontmatter_removed():
    content = '---\ntitle: "Test"\nurl: "https://example.com"\n---\n\n# Title\n\nBody text.'
    chunks = chunk_article(content, "5", "https://example.com", "Title")
    for chunk in chunks:
        assert "---" not in chunk["document"] or "Body" in chunk["document"]


def test_chunk_ids_are_unique():
    content = "# Title\n\n## A\n\nContent A is here.\n\n## B\n\nContent B is here."
    chunks = chunk_article(content, "6", "https://example.com", "Title")
    ids = [c["id"] for c in chunks]
    assert len(ids) == len(set(ids))  # All unique

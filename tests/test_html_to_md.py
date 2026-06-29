"""Tests for HTML to Markdown converter."""

from src.html_to_md import format_article, html_to_markdown


def test_strips_scripts():
    html = "<p>Hello world</p><script>evil()</script>"
    result = html_to_markdown(html)
    assert "evil" not in result
    assert "Hello world" in result


def test_strips_iframes():
    html = "<p>Content</p><iframe src='https://evil.com'></iframe>"
    result = html_to_markdown(html)
    assert "iframe" not in result
    assert "Content" in result


def test_converts_headings():
    html = "<h2>My Title</h2><p>Body text here.</p>"
    md = html_to_markdown(html)
    assert "## My Title" in md
    assert "Body text here." in md


def test_converts_links():
    html = '<p>Visit <a href="https://example.com">Example</a></p>'
    md = html_to_markdown(html)
    assert "[Example](https://example.com)" in md


def test_converts_lists():
    html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
    md = html_to_markdown(html)
    assert "- Item 1" in md
    assert "- Item 2" in md


def test_converts_code_blocks():
    html = "<pre><code>print('hello')</code></pre>"
    md = html_to_markdown(html)
    assert "print('hello')" in md


def test_empty_input():
    assert html_to_markdown("") == ""
    assert html_to_markdown(None) == ""


def test_cleans_excessive_newlines():
    html = "<p>One</p><br><br><br><br><p>Two</p>"
    md = html_to_markdown(html)
    assert "\n\n\n" not in md


def test_format_article_has_frontmatter():
    article = {
        "title": "Test Article",
        "html_url": "https://example.com/article",
        "updated_at": "2026-01-01T00:00:00Z",
        "body": "<h2>Section</h2><p>Content</p>",
    }
    result = format_article(article)
    assert "---" in result
    assert 'title: "Test Article"' in result
    assert 'url: "https://example.com/article"' in result
    assert "# Test Article" in result
    assert "## Section" in result


def test_format_article_escapes_quotes_in_title():
    article = {
        "title": 'Article with "quotes"',
        "html_url": "",
        "updated_at": "",
        "body": "<p>Body</p>",
    }
    result = format_article(article)
    assert '\\"quotes\\"' in result

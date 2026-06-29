"""HTML to clean Markdown converter for Zendesk articles."""

import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md


def html_to_markdown(html: str) -> str:
    """Convert article HTML body to clean Markdown.

    Strips nav, ads, scripts, iframes. Preserves headings, lists, links,
    code blocks.
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "iframe"]):
        tag.decompose()

    # Convert to markdown preserving structure
    # Note: markdownify doesn't allow both strip and convert params
    markdown = md(
        str(soup),
        heading_style="ATX",
        bullets="-",
        strip=["img"],
    )

    # Clean up excessive whitespace (markdownify can produce many newlines from <br> tags)
    # First strip trailing whitespace on lines (removes markdown line-break markers)
    markdown = re.sub(r" +\n", "\n", markdown)
    # Then collapse excessive newlines
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    return markdown.strip()


def format_article(article: dict) -> str:
    """Format a Zendesk article dict into a Markdown file with frontmatter.

    Frontmatter includes title, URL, and updated_at for citation and
    delta detection.
    """
    title = article.get("title", "Untitled")
    url = article.get("html_url", "")
    updated = article.get("updated_at", "")
    body_html = article.get("body", "")

    body_md = html_to_markdown(body_html)

    # Escape quotes in title for valid YAML
    safe_title = title.replace('"', '\\"')

    return (
        f'---\n'
        f'title: "{safe_title}"\n'
        f'url: "{url}"\n'
        f'updated_at: "{updated}"\n'
        f'---\n\n'
        f'# {title}\n\n'
        f'{body_md}\n'
    )

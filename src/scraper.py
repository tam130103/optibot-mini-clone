"""Zendesk Help Center API scraper for OptiSigns support articles."""

import hashlib
import logging
import os
import re
import time

import requests

from src.html_to_md import format_article

logger = logging.getLogger(__name__)


def fetch_all_articles(base_url: str) -> list[dict]:
    """Fetch all public articles from Zendesk Help Center API.

    Uses offset pagination (next_page). Skips drafts.
    Returns list of article dicts with id, title, html_url, body, updated_at.
    """
    url = f"https://{base_url}/api/v2/help_center/en-us/articles.json"
    params = {"per_page": 100}
    articles = []

    page = 0
    while url:
        page += 1
        logger.info(f"Fetching page {page}...")

        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        page_articles = [
            a for a in data.get("articles", [])
            if not a.get("draft", False)
        ]
        articles.extend(page_articles)
        logger.info(f"  Got {len(page_articles)} articles (total: {len(articles)})")

        url = data.get("next_page")
        params = {}  # next_page URL already has params baked in

        if url:
            time.sleep(0.5)  # Respect rate limits

    logger.info(f"Fetched {len(articles)} published articles total")
    return articles


def slugify(title: str) -> str:
    """Convert article title to filesystem-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:80]


def save_articles(articles: list[dict], output_dir: str) -> dict[str, str]:
    """Save articles as Markdown files.

    Returns dict of {article_id: content_sha256_hash} for delta detection.
    """
    os.makedirs(output_dir, exist_ok=True)
    hashes = {}

    for article in articles:
        article_id = str(article["id"])
        slug = slugify(article["title"])
        filename = f"{article_id}-{slug}.md"
        content = format_article(article)

        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        hashes[article_id] = hashlib.sha256(content.encode()).hexdigest()

    logger.info(f"Saved {len(articles)} articles to {output_dir}")
    return hashes

"""Daily job entrypoint: scrape → detect changes → upload delta to vector store."""

import logging
import sys

from src.config import ARTICLES_DIR, STATE_FILE, ZENDESK_BASE
from src.delta import compute_delta, load_state, save_state
from src.scraper import fetch_all_articles, save_articles
from src.vector_store import delete_articles, upsert_articles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Run the full scrape-detect-upload pipeline.

    Returns 0 on success for clean Docker exit code.
    """
    logger.info("=" * 60)
    logger.info("  OptiBot Scraper — Starting")
    logger.info("=" * 60)

    # 1. Load previous state
    old_hashes = load_state(STATE_FILE)
    logger.info(f"Previous state: {len(old_hashes)} articles tracked")

    # 2. Scrape all articles from Zendesk
    articles = fetch_all_articles(ZENDESK_BASE)
    logger.info(f"Scraped {len(articles)} published articles")

    # 3. Save to disk and compute content hashes
    new_hashes = save_articles(articles, ARTICLES_DIR)

    # 4. Compute delta (added/updated/skipped/removed)
    delta = compute_delta(old_hashes, new_hashes)

    # 5. Upload only changed articles to vector store
    changed_ids = delta["added"] + delta["updated"]

    if changed_ids:
        logger.info(
            f"Uploading {len(changed_ids)} changed articles to vector store..."
        )
        stats = upsert_articles(ARTICLES_DIR, article_ids=changed_ids)
        logger.info(f"Vector store updated: {stats}")
    else:
        logger.info("No changes detected — vector store is up to date")

    # 6. Remove deleted/unpublished articles from vector store
    removed_ids = delta["removed"]
    if removed_ids:
        logger.info(f"Removing {len(removed_ids)} deleted articles from vector store...")
        delete_articles(removed_ids)

    # 7. Save new state for next run
    save_state(STATE_FILE, new_hashes)

    # 8. Summary
    logger.info("=" * 60)
    logger.info("  Summary")
    logger.info("=" * 60)
    logger.info(f"  Total articles:  {len(articles)}")
    logger.info(f"  Added:           {len(delta['added'])}")
    logger.info(f"  Updated:         {len(delta['updated'])}")
    logger.info(f"  Skipped:         {len(delta['skipped'])}")
    logger.info(f"  Removed:         {len(delta['removed'])}")
    logger.info("=" * 60)
    logger.info("  Done")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

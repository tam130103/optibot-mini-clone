"""Hash-based delta detection for article change tracking."""

import json
import logging
import os

logger = logging.getLogger(__name__)


def load_state(state_file: str) -> dict[str, str]:
    """Load previous article hash state from JSON file.

    Returns dict of {article_id: content_sha256_hash}.
    """
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state_file: str, hashes: dict[str, str]):
    """Save current article hash state to JSON file."""
    os.makedirs(os.path.dirname(state_file) or ".", exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2)
    logger.info(f"Saved state with {len(hashes)} article hashes")


def compute_delta(
    old_hashes: dict[str, str], new_hashes: dict[str, str]
) -> dict:
    """Compare old and new hashes to find changes.

    Returns dict with keys: added, updated, skipped, removed.
    Each value is a list of article_id strings.
    """
    added = [k for k in new_hashes if k not in old_hashes]
    updated = [
        k
        for k in new_hashes
        if k in old_hashes and new_hashes[k] != old_hashes[k]
    ]
    skipped = [
        k
        for k in new_hashes
        if k in old_hashes and new_hashes[k] == old_hashes[k]
    ]
    removed = [k for k in old_hashes if k not in new_hashes]

    logger.info(
        f"Delta: {len(added)} added, {len(updated)} updated, "
        f"{len(skipped)} skipped, {len(removed)} removed"
    )
    return {
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "removed": removed,
    }

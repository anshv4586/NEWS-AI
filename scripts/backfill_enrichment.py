"""
Backfill & Migration Script for Global News AI - Phase 3

Fetches existing records from MySQL, processes and enriches them
using src.news_processor, and updates the database records in-place.

Run with:
    python scripts/backfill_enrichment.py
"""

import logging
import sys
from collections import Counter
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.database import test_connection, get_connection
from src.news_processor import process_article
from src.news_repository import update_article_enrichment, get_latest_news

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logger = logging.getLogger(__name__)


def backfill_existing_news() -> int:
    """
    Safely enriches and updates existing news records in MySQL.
    """
    logger.info("Starting Phase 3 Backfill & Enrichment for Existing Records...")

    if not test_connection():
        logger.error("Database connection failed. Backfill aborted.")
        return 1

    # Fetch all existing articles from MySQL
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, article_id, title, summary, url, source, published_at, author, category, language FROM news;")
        existing_articles = cursor.fetchall()
        cursor.close()
    finally:
        conn.close()

    total_articles = len(existing_articles)
    logger.info(f"Retrieved {total_articles} existing articles from MySQL.")

    if total_articles == 0:
        logger.info("No existing records to backfill.")
        return 0

    updated_count = 0
    quality_counts = Counter()
    category_counts = Counter()
    country_counts = Counter()
    language_counts = Counter()

    for art in existing_articles:
        processed, status_msg = process_article(art)
        if processed:
            art_id = str(art["article_id"])
            success = update_article_enrichment(art_id, processed)
            if success:
                updated_count += 1
                quality_counts[processed["quality_status"]] += 1
                category_counts[processed["category"]] += 1
                country_counts[processed["country"]] += 1
                language_counts[processed["language"]] += 1
        else:
            quality_counts["invalid"] += 1
            logger.warning(f"Article ID {art.get('id')} failed processing: {status_msg}")

    print("\n" + "=" * 78)
    print(" PHASE 3 ENRICHMENT BACKFILL SUMMARY")
    print("=" * 78)
    print(f" Total Existing Records Processed : {total_articles}")
    print(f" Successfully Updated in MySQL   : {updated_count}")
    print("-" * 78)
    print(f" Quality Status Breakdown : {dict(quality_counts)}")
    print(f" Category Breakdown       : {dict(category_counts)}")
    print(f" Country Breakdown        : {dict(country_counts)}")
    print(f" Language Breakdown       : {dict(language_counts)}")
    print("=" * 78 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(backfill_existing_news())

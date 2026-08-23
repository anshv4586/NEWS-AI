"""
Main Pipeline Entry Point for Global News AI - Phase 3 (News Processing & Enrichment)

Coordinates RSS collection, text normalization, article validation,
metadata enrichment (language, category, country, keywords, quality),
MySQL persistence, and CSV/JSON backup storage with full logging and error isolation.

Run executable with:
    python -m src.main
"""

import logging
import sys
from collections import Counter
from config.feeds import RSS_FEEDS
from src.cleaner import deduplicate_articles
from src.rss_collector import collect_all_feeds
from src.storage import save_articles
from src.database import test_connection
from src.news_processor import process_article
from src.news_repository import insert_many_news, get_latest_news

# Configure standardized logger format
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def run_pipeline() -> int:
    """
    Executes the Phase 3 Global News AI Pipeline:
    RSS Collection -> Processing & Enrichment -> Deduplication -> MySQL Storage -> CSV/JSON Backup.
    """
    logger.info("Starting Global News AI Pipeline (Phase 3 - News Processing & Enrichment)...")

    # Step 0: Test Database Connection
    db_available = test_connection()
    if not db_available:
        logger.error("MySQL Database is unavailable. Pipeline will proceed in offline mode.")

    try:
        # Step 1: Collect Raw Articles from RSS Feeds
        raw_articles = collect_all_feeds(RSS_FEEDS)
        logger.info(f"Total raw articles retrieved from RSS feeds: {len(raw_articles)}")

        if not raw_articles:
            logger.warning("No articles collected from any feed. Pipeline stopping.")
            return 1

        # Step 2: Processing & Enrichment (Validation, Cleaning, Normalization, Enrichment)
        processed_articles = []
        rejected_count = 0
        quality_counter = Counter()

        for art in raw_articles:
            processed, status_msg = process_article(art)
            if processed:
                processed_articles.append(processed)
                quality_counter[processed["quality_status"]] += 1
            else:
                rejected_count += 1
                logger.warning(f"Rejected article '{art.get('title', 'No Title')}': {status_msg}")

        logger.info(
            f"Processing Complete -> Valid Enriched: {len(processed_articles)} | Rejected: {rejected_count}"
        )

        # Step 3: Remove In-Memory Duplicates
        unique_articles = deduplicate_articles(processed_articles)
        in_memory_duplicates = len(processed_articles) - len(unique_articles)
        logger.info(
            f"Filtered {in_memory_duplicates} in-memory duplicates ({len(unique_articles)} unique remaining)."
        )

        # Step 4: MySQL Persistence (Enriched Data Storage)
        db_stats = {"inserted": 0, "skipped": 0, "total": len(unique_articles)}
        if db_available:
            try:
                db_stats = insert_many_news(unique_articles)
                logger.info(
                    f"MySQL Ingestion Complete -> Inserted: {db_stats['inserted']} new articles | Skipped: {db_stats['skipped']} duplicates."
                )
            except Exception as db_err:
                logger.error(f"MySQL insertion error (continuing with CSV/JSON backup): {db_err}")

        # Step 5: Backup Storage (CSV & JSON export)
        storage_info = save_articles(unique_articles, "data")
        logger.info(f"Saved backup dataset to CSV  : {storage_info['csv']}")
        logger.info(f"Saved backup dataset to JSON : {storage_info['json']}")

        logger.info("Phase 3 Collection & Processing completed successfully!")

        # Step 6: Terminal Execution Summary & Enriched Article Preview
        print("\n" + "=" * 78)
        print(" GLOBAL NEWS AI - PHASE 3 PIPELINE EXECUTION SUMMARY")
        print("=" * 78)
        print(f" Raw RSS Articles Collected    : {len(raw_articles)}")
        print(f" Valid Enriched Articles       : {len(processed_articles)}")
        print(f" Rejected Articles             : {rejected_count}")
        print(f" Unique Batch Articles         : {len(unique_articles)}")
        print(f" MySQL Newly Inserted          : {db_stats['inserted']}")
        print(f" MySQL Duplicates Skipped       : {db_stats['skipped']}")
        print(f" Quality Ratings Distribution  : {dict(quality_counter)}")
        print("-" * 78)
        print(" TOP 5 LATEST ENRICHED ARTICLES IN MYSQL DATABASE")
        print("-" * 78)

        preview_articles = get_latest_news(limit=5) if db_available else unique_articles[:5]

        for i, art in enumerate(preview_articles, 1):
            summary = (art.get("summary") or "").strip()
            if len(summary) > 120:
                summary = summary[:117] + "..."

            print(f" {i}. [{art.get('source', 'Unknown')}] ({art.get('category', 'World')}) - Country: {art.get('country', 'Global')} | Lang: {art.get('language', 'English')}")
            print(f"    Title:    {art.get('title')}")
            print(f"    Keywords: {art.get('keywords')}")
            print(f"    Quality:  {art.get('quality_status')} | Published: {art.get('published_at')}")
            print(f"    URL:      {art.get('url')}")
            print("-" * 78)

        print(" Enriched backup dataset saved in data/news.csv and data/news.json\n")
        return 0

    except Exception as e:
        logger.error(f"Unexpected pipeline execution error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(run_pipeline())

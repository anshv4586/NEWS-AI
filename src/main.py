"""
Main Pipeline Entry Point for Global News AI - Phase 1

Coordinates RSS feed ingestion, data extraction, cleaning, deduplication, and storage
with clear logging, error isolation, and terminal headline preview.

Run executable with:
    python -m src.main
"""

import logging
import sys
from config.feeds import RSS_FEEDS
from src.cleaner import clean_articles_list, deduplicate_articles
from src.rss_collector import collect_all_feeds
from src.storage import save_articles

# Configure standardized logger format
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def run_pipeline() -> int:
    """
    Executes the Phase 1 RSS News Collection Pipeline with logging, error handling,
    and a sample headline preview.
    """
    logger.info("Starting RSS News Collection...")

    try:
        # Step 1: Collect Raw Articles from Configured Feeds
        raw_articles = collect_all_feeds(RSS_FEEDS)
        logger.info(f"Total raw articles retrieved: {len(raw_articles)}")

        if not raw_articles:
            logger.warning("No articles collected from any feed. Pipeline stopping.")
            return 1

        # Step 2: Clean Data
        cleaned_articles = clean_articles_list(raw_articles)
        logger.info(f"Cleaned {len(cleaned_articles)} valid articles.")

        # Step 3: Remove Duplicates
        unique_articles = deduplicate_articles(cleaned_articles)
        duplicates_removed = len(cleaned_articles) - len(unique_articles)
        logger.info(
            f"Removed {duplicates_removed} duplicate articles ({len(unique_articles)} unique remaining)."
        )

        # Step 4: Storage
        storage_info = save_articles(unique_articles, "data")
        logger.info(f"Saved articles to CSV  : {storage_info['csv']}")
        logger.info(f"Saved articles to JSON : {storage_info['json']}")

        logger.info("Collection completed successfully!")
        logger.info(f"Total unique articles collected and saved: {storage_info['count']}")

        # Step 5: Terminal Headline Preview with Summary
        print("\n" + "=" * 75)
        print(" TOP 5 COLLECTED NEWS HEADLINES PREVIEW")
        print("=" * 75)
        for i, art in enumerate(unique_articles[:5], 1):
            summary = art.get("summary", "").strip()
            if len(summary) > 140:
                summary = summary[:137] + "..."

            print(f" {i}. [{art['source']}] ({art['category'].upper()})")
            print(f"    Title:   {art['title']}")
            print(f"    Summary: {summary if summary else 'No summary available.'}")
            print(f"    Date:    {art['published_at']}")
            print(f"    URL:     {art['url']}")
            print("-" * 75)
        print(" Full dataset is saved in data/news.csv and data/news.json\n")

        return 0

    except Exception as e:
        logger.error(f"Unexpected pipeline execution error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(run_pipeline())

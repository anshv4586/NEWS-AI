"""
Step 8 Verification Test: Duplicate Detection
"""

from config.feeds import RSS_FEEDS
from src.cleaner import clean_articles_list, deduplicate_articles
from src.rss_collector import collect_all_feeds


def test_deduplication():
    print("Fetching raw articles...")
    raw_articles = collect_all_feeds(RSS_FEEDS)
    print(f"Total raw articles collected: {len(raw_articles)}")

    cleaned = clean_articles_list(raw_articles)
    print(f"Total cleaned valid articles: {len(cleaned)}")

    # Add artificial duplicate to test detection explicitly
    if cleaned:
        duplicate_sample = cleaned[0].copy()
        cleaned.append(duplicate_sample)
        print(
            f"Added 1 artificial duplicate article (Total before deduplication: {len(cleaned)})"
        )

    deduped = deduplicate_articles(cleaned)
    duplicates_removed = len(cleaned) - len(deduped)

    print("\n=== DEDUPLICATION RESULTS ===")
    print(f"Articles before deduplication : {len(cleaned)}")
    print(f"Articles after deduplication  : {len(deduped)}")
    print(f"Duplicates detected & removed : {duplicates_removed}")
    print("================================")


if __name__ == "__main__":
    test_deduplication()

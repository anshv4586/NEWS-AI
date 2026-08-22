"""
Step 9 Verification Test: Data Storage Module
"""

from pathlib import Path
from config.feeds import RSS_FEEDS
from src.cleaner import clean_articles_list, deduplicate_articles
from src.rss_collector import collect_all_feeds
from src.storage import save_articles


def test_storage():
    print("Collecting, cleaning, and deduplicating news...")
    raw = collect_all_feeds(RSS_FEEDS)
    cleaned = clean_articles_list(raw)
    deduped = deduplicate_articles(cleaned)

    print(f"Saving {len(deduped)} articles to disk...")
    result = save_articles(deduped, "data")

    csv_path = Path(result["csv"])
    json_path = Path(result["json"])

    print("\n=== STORAGE RESULTS ===")
    print(f"CSV File Exists  : {csv_path.exists()} ({csv_path})")
    print(f"JSON File Exists : {json_path.exists()} ({json_path})")
    print(f"CSV Size         : {csv_path.stat().st_size / 1024:.2f} KB")
    print(f"JSON Size        : {json_path.stat().st_size / 1024:.2f} KB")
    print(f"Articles Saved   : {result['count']}")
    print("=========================")


if __name__ == "__main__":
    test_storage()

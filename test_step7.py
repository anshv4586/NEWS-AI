"""
Step 7 Verification Test: Data Cleaner Module
"""

from config.feeds import RSS_FEEDS
from src.cleaner import clean_articles_list
from src.rss_collector import collect_all_feeds


def test_cleaner():
    print("Fetching raw articles...")
    raw_articles = collect_all_feeds(RSS_FEEDS)
    print(f"Raw articles collected: {len(raw_articles)}\n")

    print("Cleaning articles...")
    cleaned_articles = clean_articles_list(raw_articles)
    print(f"Cleaned valid articles: {len(cleaned_articles)}\n")

    if raw_articles and cleaned_articles:
        print("=== BEFORE vs AFTER CLEANING COMPARISON ===")
        raw_sample = raw_articles[0]
        cleaned_sample = cleaned_articles[0]

        print(f"RAW Published At : {raw_sample['published_at']}")
        print(f"CLEAN Published At: {cleaned_sample['published_at']}\n")

        print(f"RAW URL  : {raw_sample['url']}")
        print(f"CLEAN URL: {cleaned_sample['url']}\n")

        print(f"CLEAN Title  : {cleaned_sample['title']}")
        print(f"CLEAN Summary: {cleaned_sample['summary'][:120]}...")
        print(f"CLEAN Author : {cleaned_sample['author']}")
        print("===========================================")


if __name__ == "__main__":
    test_cleaner()

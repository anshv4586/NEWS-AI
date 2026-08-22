"""
Step 6 Verification Test: RSS Collector Module
"""

from config.feeds import RSS_FEEDS
from src.rss_collector import collect_all_feeds


def test_collector():
    print("Testing RSS Collector module across all configured feeds...\n")
    articles = collect_all_feeds(RSS_FEEDS)

    print(f"Total structured articles collected: {len(articles)}\n")

    if articles:
        print("--- Sample Extracted Article Structure ---")
        sample = articles[0]
        for key, value in sample.items():
            print(f"{key:15}: {value}")
        print("------------------------------------------")


if __name__ == "__main__":
    test_collector()

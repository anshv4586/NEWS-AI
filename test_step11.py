"""
Step 11 Verification Test: Error Handling and Fault Tolerance
"""

import logging
import sys
from src.rss_collector import collect_all_feeds

# Configure logger output for test
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def test_fault_tolerance():
    print("Testing Fault Tolerance with broken & valid RSS URLs...\n")

    test_feeds = {
        "world": [
            {
                "source": "BBC News (Valid)",
                "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
            },
            {
                "source": "Broken Source (Invalid URL)",
                "url": "http://invalid-nonexistent-domain-12345.com/rss.xml",
            },
        ]
    }

    articles = collect_all_feeds(test_feeds)

    print(f"\nTotal articles recovered despite broken feed: {len(articles)}")
    assert len(articles) > 0, "Pipeline should still collect articles from valid feeds!"
    print("Fault tolerance test PASSED! Broken feed did NOT stop collection.\n")


if __name__ == "__main__":
    test_fault_tolerance()

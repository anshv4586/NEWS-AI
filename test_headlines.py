"""
Step 5: Quick RSS Headline Printer

A minimal script to demonstrate downloading and parsing RSS headlines live using feedparser.
"""

import feedparser
from config.feeds import RSS_FEEDS


def print_sample_headlines():
    # Select the first feed from our configuration
    category = "world"
    feed_info = RSS_FEEDS[category][0]
    source_name = feed_info["source"]
    url = feed_info["url"]

    print(f"Fetching RSS Feed: [{source_name}] ({category.upper()})")
    print(f"URL: {url}\n")

    # Download and parse XML feed
    feed = feedparser.parse(url)

    # Display Feed Metadata
    print(f"Header Title: {feed.feed.get('title', 'N/A')}")
    print(f"Articles Found: {len(feed.entries)}\n")
    print("=" * 60)
    print("TOP 5 LIVE HEADLINES")
    print("=" * 60)

    # Print first 5 article headlines
    for i, entry in enumerate(feed.entries[:5], 1):
        title = entry.get("title", "No Title")
        published = entry.get("published", entry.get("updated", "No Date"))
        link = entry.get("link", "No Link")

        print(f"{i}. {title}")
        print(f"   Published: {published}")
        print(f"   Link:      {link}")
        print("-" * 60)


if __name__ == "__main__":
    print_sample_headlines()

"""
RSS Feed Configuration for Global News AI

This file centralizes all news sources. Each RSS feed is categorized and explicitly
identifies the news publisher (source) and RSS endpoint URL.
"""

RSS_FEEDS = {
    "world": [
        {
            "source": "BBC News",
            "url": "http://feeds.bbci.co.uk/news/world/rss.xml"
        },
        {
            "source": "Al Jazeera",
            "url": "https://www.aljazeera.com/xml/rss/all.xml"
        }
    ],
    "technology": [
        {
            "source": "BBC News",
            "url": "http://feeds.bbci.co.uk/news/technology/rss.xml"
        }
    ],
    "business": [
        {
            "source": "BBC News",
            "url": "http://feeds.bbci.co.uk/news/business/rss.xml"
        }
    ]
}

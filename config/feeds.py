"""
RSS Feed Configuration for Global News AI

Centralizes all active breaking news sources categorized by topic and publisher.
Prioritizes high-frequency, reliable global and national news endpoints.
"""

RSS_FEEDS = {
    "world": [
        {
            "source": "BBC World News",
            "url": "http://feeds.bbci.co.uk/news/world/rss.xml"
        },
        {
            "source": "BBC Top Stories",
            "url": "http://feeds.bbci.co.uk/news/rss.xml"
        },
        {
            "source": "Al Jazeera",
            "url": "https://www.aljazeera.com/xml/rss/all.xml"
        },
        {
            "source": "Google News World",
            "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        }
    ],
    "india": [
        {
            "source": "Google News India",
            "url": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
        },
        {
            "source": "Times of India",
            "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
        },
        {
            "source": "The Hindu",
            "url": "https://www.thehindu.com/news/national/feeder/default.rss"
        },
        {
            "source": "NDTV News",
            "url": "https://feeds.feedburner.com/ndtvnews-top-stories"
        }
    ],
    "technology": [
        {
            "source": "TechCrunch",
            "url": "https://techcrunch.com/feed/"
        },
        {
            "source": "BBC Technology",
            "url": "http://feeds.bbci.co.uk/news/technology/rss.xml"
        },
        {
            "source": "The Verge",
            "url": "https://www.theverge.com/rss/index.xml"
        },
        {
            "source": "Wired",
            "url": "https://www.wired.com/feed/rss"
        }
    ],
    "business": [
        {
            "source": "BBC Business",
            "url": "http://feeds.bbci.co.uk/news/business/rss.xml"
        },
        {
            "source": "CNBC News",
            "url": "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=rss"
        },
        {
            "source": "Google News Business",
            "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
        }
    ],
    "sports": [
        {
            "source": "BBC Sport",
            "url": "http://feeds.bbci.co.uk/sport/rss.xml"
        },
        {
            "source": "Google News Sports",
            "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
        }
    ],
    "climate": [
        {
            "source": "BBC Science & Environment",
            "url": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml"
        },
        {
            "source": "Phys.org Earth News",
            "url": "https://phys.org/rss-feed/earth-news/"
        }
    ]
}


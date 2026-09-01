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
        },
        {
            "source": "CNN World",
            "url": "http://rss.cnn.com/rss/edition_world.rss"
        },
        {
            "source": "NPR News",
            "url": "https://feeds.npr.org/1001/rss.xml"
        },
        {
            "source": "DW World News",
            "url": "https://rss.dw.com/rdf/rss-en-all"
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
        },
        {
            "source": "Hindustan Times",
            "url": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml"
        },
        {
            "source": "Indian Express",
            "url": "https://indianexpress.com/feed/"
        },
        {
            "source": "LiveMint",
            "url": "https://www.livemint.com/rss/news"
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
        },
        {
            "source": "Ars Technica",
            "url": "https://feeds.arstechnica.com/arstechnica/index"
        },
        {
            "source": "Engadget",
            "url": "https://www.engadget.com/rss.xml"
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
        },
        {
            "source": "MarketWatch",
            "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories"
        },
        {
            "source": "Yahoo Finance",
            "url": "https://finance.yahoo.com/news/rssindex"
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
        },
        {
            "source": "ESPN",
            "url": "https://www.espn.com/espn/rss/news"
        },
        {
            "source": "Sky Sports",
            "url": "https://www.skysports.com/rss/12040"
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
        },
        {
            "source": "ScienceDaily",
            "url": "https://www.sciencedaily.com/rss/top/science.xml"
        },
        {
            "source": "NASA News",
            "url": "https://www.nasa.gov/news-release/feed/"
        }
    ]
}

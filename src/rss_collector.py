"""
RSS Collector Module for Global News AI

Fetches and extracts structured article dictionaries from RSS feed URLs with error handling and logging.
"""

from typing import Any, Dict, List
import logging
import feedparser

logger = logging.getLogger(__name__)


def extract_article_fields(
    entry: Dict[str, Any], source_name: str, category_name: str
) -> Dict[str, Any]:
    """
    Extracts raw RSS entry fields into a standard dictionary schema safely.
    """
    title = str(entry.get("title", "")).strip()
    summary = str(entry.get("summary", entry.get("description", ""))).strip()
    url = str(entry.get("link", "")).strip()
    published_at = str(entry.get("published", entry.get("updated", ""))).strip()
    author = str(entry.get("author", "")).strip()

    return {
        "title": title,
        "summary": summary,
        "url": url,
        "source": source_name,
        "published_at": published_at,
        "author": author,
        "category": category_name,
        "language": "English",
    }


def fetch_feed_articles(
    url: str, source_name: str, category_name: str
) -> List[Dict[str, Any]]:
    """
    Downloads an RSS feed URL with error handling for timeouts, invalid URLs, and network failures.
    """
    articles = []
    logger.info(f"Processing {category_name.capitalize()} - {source_name}")

    try:
        # feedparser handles connection timeouts and HTTP status internally
        parsed_feed = feedparser.parse(url)

        # Check for HTTP status errors (e.g. 404, 500)
        status = getattr(parsed_feed, "status", None)
        if status and status >= 400:
            logger.warning(f"HTTP Error {status} when accessing feed: {url}")
            return []

        # Check for XML bozo parsing exceptions
        if getattr(parsed_feed, "bozo", 0) == 1:
            bozo_exc = getattr(parsed_feed, "bozo_exception", "Unknown Parsing Error")
            logger.warning(f"Malformed feed notice at {url}: {bozo_exc}")

        entries = getattr(parsed_feed, "entries", [])
        for entry in entries:
            try:
                article = extract_article_fields(entry, source_name, category_name)
                if article["title"] or article["url"]:
                    articles.append(article)
            except Exception as item_err:
                logger.debug(f"Skipping malformed entry in {url}: {item_err}")

        logger.info(f"Retrieved {len(articles)} articles from {source_name}")

    except Exception as e:
        logger.warning(f"Failed to process feed ({source_name} - {url}): {e}")
        return []

    return articles


def collect_all_feeds(
    feeds_config: Dict[str, List[Dict[str, str]]]
) -> List[Dict[str, Any]]:
    """
    Iterates over all configured feeds, safely collecting articles even if individual feeds fail.
    """
    all_articles = []

    for category, feeds in feeds_config.items():
        for feed_info in feeds:
            source = feed_info.get("source", "Unknown Source")
            url = feed_info.get("url", "")

            if not url:
                logger.warning(f"Skipping invalid feed configuration with missing URL in category '{category}'")
                continue

            articles = fetch_feed_articles(url, source, category)
            all_articles.extend(articles)

    return all_articles

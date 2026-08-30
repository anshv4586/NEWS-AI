"""
RSS Collector Module for Global News AI

Fetches and extracts structured article dictionaries from RSS feed URLs with
multi-threaded parallel collection, strict socket timeouts, and error handling.
"""

from typing import Any, Dict, List, Optional
import socket
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import feedparser

logger = logging.getLogger(__name__)

# Enforce strict 3.5-second default socket timeout so hung URLs fail fast
socket.setdefaulttimeout(3.5)


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
        parsed_feed = feedparser.parse(
            url,
            request_headers={"User-Agent": "GlobalNewsAI/1.0 (News Aggregator)"}
        )

        # Check for HTTP status errors (e.g. 404, 500)
        status = getattr(parsed_feed, "status", None)
        if status and status >= 400:
            logger.warning(f"HTTP Error {status} when accessing feed: {url}")
            return []

        # Check for XML bozo parsing exceptions
        if getattr(parsed_feed, "bozo", 0) == 1:
            bozo_exc = getattr(parsed_feed, "bozo_exception", "Unknown Parsing Error")
            logger.debug(f"Malformed feed notice at {url}: {bozo_exc}")

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
    feeds_config: Dict[str, List[Dict[str, str]]],
    max_workers: int = 8,
    timeout_seconds: float = 4.0,
) -> List[Dict[str, Any]]:
    """
    Parallel multi-threaded collector:
    Spawns worker threads to fetch all feeds simultaneously within timeout_seconds,
    preventing slow feeds from delaying the response.
    """
    all_articles = []
    tasks = []

    # Flatten feeds into a list of tuples: (url, source, category)
    feed_items = []
    for category, feeds in feeds_config.items():
        for feed_info in feeds:
            source = feed_info.get("source", "Unknown Source")
            url = feed_info.get("url", "")
            if url:
                feed_items.append((url, source, category))

    if not feed_items:
        return []

    workers = min(max_workers, len(feed_items))
    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_feed = {
                executor.submit(fetch_feed_articles, url, src, cat): (src, url)
                for url, src, cat in feed_items
            }

            for future in as_completed(future_to_feed, timeout=timeout_seconds):
                try:
                    feed_articles = future.result()
                    if feed_articles:
                        all_articles.extend(feed_articles)
                except Exception as exc:
                    src_name, feed_url = future_to_feed[future]
                    logger.warning(f"Feed {src_name} ({feed_url}) generated an exception: {exc}")
    except TimeoutError:
        logger.warning(f"Parallel feed collection reached {timeout_seconds}s deadline. Returning gathered articles ({len(all_articles)} items).")
    except Exception as general_err:
        logger.error(f"Error during parallel feed collection: {general_err}")

    return all_articles

"""
Data Cleaner & Deduplication Module for Global News AI

Provides functions to clean HTML, normalize text/whitespace, format publication dates,
clean tracking parameters from URLs, validate article fields, and remove duplicates.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
import re


def clean_html(raw_html: str) -> str:
    """
    Strips raw HTML tags and decodes HTML entities (&amp;, &quot;, etc.).
    """
    if not raw_html:
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")
    cleaned_text = soup.get_text(separator=" ")
    return cleaned_text


def clean_whitespace(text: str) -> str:
    """
    Replaces multiple spaces, newlines, tabs, and non-breaking spaces with a single clean space.
    """
    if not text:
        return ""

    cleaned = re.sub(r"\s+", " ", text)
    return cleaned.strip()


def normalize_date(date_string: str) -> str:
    """
    Parses heterogeneous RSS date strings into standard ISO format (YYYY-MM-DD HH:MM:SS).
    Returns empty string if parsing fails.
    """
    if not date_string:
        return ""

    try:
        dt = date_parser.parse(date_string)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OverflowError):
        return ""


def normalize_url(url: str) -> str:
    """
    Cleans tracking query parameters (e.g., utm_source, at_medium) from URLs.
    """
    if not url:
        return ""

    parsed = urlparse(url.strip())
    query_params = parsed.query.split("&")
    clean_params = [
        p for p in query_params if not p.startswith(("utm_", "at_"))
    ]
    new_query = "&".join(clean_params)

    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))
    return clean_url


def clean_article(article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Cleans all fields of a single raw article dictionary.
    Returns None if the article is invalid (missing title or url).
    """
    raw_title = clean_html(article.get("title", ""))
    raw_summary = clean_html(article.get("summary", ""))

    title = clean_whitespace(raw_title)
    summary = clean_whitespace(raw_summary)
    url = normalize_url(article.get("url", ""))

    # Invalid check: must have a headline and a URL
    if not title or not url:
        return None

    published_at = normalize_date(article.get("published_at", ""))
    author = clean_whitespace(clean_html(article.get("author", "")))
    if not author:
        author = "Unknown"

    return {
        "title": title,
        "summary": summary,
        "url": url,
        "source": article.get("source", "Unknown"),
        "published_at": published_at,
        "author": author,
        "category": article.get("category", "general"),
        "language": article.get("language", "English"),
    }


def clean_articles_list(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cleans a list of article dictionaries, discarding any invalid articles.
    """
    cleaned_list = []
    for art in articles:
        cleaned = clean_article(art)
        if cleaned is not None:
            cleaned_list.append(cleaned)
    return cleaned_list


def deduplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates articles based on:
    1. Primary key: Normalized Article URL
    2. Secondary key: Lowercased Normalized Article Title

    Preserves the first occurrence of an article while discarding duplicates.
    """
    unique_articles = []
    seen_urls = set()
    seen_titles = set()

    for article in articles:
        url_key = article.get("url", "").strip().lower()
        title_key = article.get("title", "").strip().lower()

        # Skip if either the URL or exact title was seen previously
        if url_key in seen_urls or title_key in seen_titles:
            continue

        if url_key:
            seen_urls.add(url_key)
        if title_key:
            seen_titles.add(title_key)

        unique_articles.append(article)

    return unique_articles

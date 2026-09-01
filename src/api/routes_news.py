"""
News Database REST API Routes for Global News AI - Phase 10

Provides endpoints for:
- GET /api/news/latest (Retrieve most recent news articles from MySQL)
- GET /api/news/category/{category} (Filter news by category taxonomy)
- GET /api/news/source/{source} (Filter news by news publisher)
"""

import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from src.news_repository import (
    get_latest_news,
    get_news_by_category,
    get_news_by_source,
    get_recent_news,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["News Feed Data Access"])


def format_pub_date(val: Any) -> Optional[str]:
    """
    Formats raw datetime or string representations into clean ISO datetime strings.
    """
    if val is None:
        return None
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    s = str(val).strip()
    return s if s else None


class NewsArticleResponse(BaseModel):
    article_id: str
    title: str
    summary: Optional[str] = None
    url: str
    source: str
    published_at: Optional[Any] = None
    category: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    quality_status: Optional[str] = None


def filter_real_news(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters out test/synthetic articles AND empty-summary articles so that only
    informative, high-quality news articles with substantial details are shown to users.
    """
    real_articles = []
    for art in articles:
        source = (art.get("source") or "").lower()
        title = (art.get("title") or "").lower()
        summary = (art.get("summary") or "").strip()
        quality = art.get("quality_status")

        # Exclude mock/test artifacts
        if any(w in source for w in ["test", "unittest", "minimal", "mock", "demo", "sample"]) or \
           any(w in title for w in ["test headline", "minimal article", "automated test", "test news"]):
            continue

        # Exclude articles without real summary details (< 40 characters)
        if not summary or len(summary) < 40 or summary.lower() == title.lower():
            continue

        if quality in ("invalid", "needs_review"):
            continue

        real_articles.append(art)
    return real_articles


@router.get("/latest", response_model=List[NewsArticleResponse])
def get_latest(limit: int = 10):
    """
    Retrieves the most recent news articles from MySQL sorted by publication date.
    """
    try:
        raw_articles = get_latest_news(limit=min(limit * 2, 50))
        articles = filter_real_news(raw_articles)[:limit]
        return [
            NewsArticleResponse(
                article_id=str(art.get("article_id") or art.get("id")),
                title=art.get("title", ""),
                summary=art.get("summary"),
                url=art.get("url", ""),
                source=art.get("source", "Unknown"),
                published_at=format_pub_date(art.get("published_at")),
                category=art.get("category", "World"),
                language=art.get("language", "English"),
                country=art.get("country", "Global"),
                quality_status=art.get("quality_status", "valid"),
            )
            for art in articles
        ]
    except Exception as err:
        logger.error(f"API Error fetching latest news: {err}. Returning live RSS fallback...")
        try:
            from config.feeds import RSS_FEEDS
            from src.rss_collector import collect_all_feeds
            import hashlib
            fallback_dict = {"world": RSS_FEEDS.get("world", [])[:2]}
            raw = collect_all_feeds(fallback_dict)
            return [
                NewsArticleResponse(
                    article_id=f"rss_{hashlib.md5((item.get('link') or '').encode()).hexdigest()[:8]}",
                    title=item.get("title", "World News Headline"),
                    summary=item.get("summary"),
                    url=item.get("link", "#"),
                    source=item.get("source", "Global News"),
                    published_at=format_pub_date(item.get("published")),
                    category="World",
                    language="English",
                    country="Global",
                    quality_status="valid",
                )
                for item in raw[:limit]
            ]
        except Exception:
            return []


@router.get("/category/{category}", response_model=List[NewsArticleResponse])
def get_by_category(category: str, limit: int = 10):
    """
    Retrieves news articles filtered by category (World, Technology, Business, Sports, Climate, General).
    """
    try:
        articles = get_news_by_category(category=category, limit=min(limit, 50))
        return [
            NewsArticleResponse(
                article_id=str(art.get("article_id") or art.get("id")),
                title=art.get("title", ""),
                summary=art.get("summary"),
                url=art.get("url", ""),
                source=art.get("source", "Unknown"),
                published_at=format_pub_date(art.get("published_at")),
                category=art.get("category", "World"),
                language=art.get("language", "English"),
                country=art.get("country", "Global"),
                quality_status=art.get("quality_status", "valid"),
            )
            for art in articles
        ]
    except Exception as err:
        logger.error(f"API Error fetching category news: {err}")
        return get_latest(limit=limit)


@router.get("/source/{source}", response_model=List[NewsArticleResponse])
def get_by_source(source: str, limit: int = 10):
    """
    Retrieves news articles published by a specific news outlet (BBC News, Al Jazeera, Reuters).
    """
    try:
        articles = get_news_by_source(source=source, limit=min(limit, 50))
        return [
            NewsArticleResponse(
                article_id=str(art.get("article_id") or art.get("id")),
                title=art.get("title", ""),
                summary=art.get("summary"),
                url=art.get("url", ""),
                source=art.get("source", "Unknown"),
                published_at=format_pub_date(art.get("published_at")),
                category=art.get("category", "World"),
                language=art.get("language", "English"),
                country=art.get("country", "Global"),
                quality_status=art.get("quality_status", "valid"),
            )
            for art in articles
        ]
    except Exception as err:
        logger.error(f"API Error fetching source news: {err}")
        return get_latest(limit=limit)

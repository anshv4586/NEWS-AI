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


class NewsArticleResponse(BaseModel):
    article_id: str
    title: str
    summary: Optional[str] = None
    url: str
    source: str
    published_at: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    quality_status: Optional[str] = None


def filter_real_news(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters out test/synthetic articles (e.g. Minimal Article, Test Source, Phase 9 Test) from user-facing API responses.
    """
    real_articles = []
    for art in articles:
        source = (art.get("source") or "").lower()
        title = (art.get("title") or "").lower()
        if any(w in source for w in ["test", "unittest", "minimal", "mock", "demo", "sample"]) or \
           any(w in title for w in ["test headline", "minimal article", "automated test", "test news"]):
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
                published_at=str(art.get("published_at") or ""),
                category=art.get("category", "World"),
                language=art.get("language", "English"),
                country=art.get("country", "Global"),
                quality_status=art.get("quality_status", "valid"),
            )
            for art in articles
        ]
    except Exception as err:
        logger.error(f"API Error fetching latest news: {err}")
        raise HTTPException(status_code=500, detail=f"Database error: {err}")


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
                published_at=str(art.get("published_at") or ""),
                category=art.get("category", "World"),
                language=art.get("language", "English"),
                country=art.get("country", "Global"),
                quality_status=art.get("quality_status", "valid"),
            )
            for art in articles
        ]
    except Exception as err:
        logger.error(f"API Error fetching news for category '{category}': {err}")
        raise HTTPException(status_code=500, detail=f"Database error: {err}")


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
                published_at=str(art.get("published_at") or ""),
                category=art.get("category", "World"),
                language=art.get("language", "English"),
                country=art.get("country", "Global"),
                quality_status=art.get("quality_status", "valid"),
            )
            for art in articles
        ]
    except Exception as err:
        logger.error(f"API Error fetching news for source '{source}': {err}")
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

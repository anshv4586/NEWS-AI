"""
News Repository (DAO) Module for Global News AI - Phase 3 (Enriched Data Access)

Handles object-to-relational mapping, parametrized MySQL queries,
duplicate prevention via UNIQUE URL constraints (INSERT IGNORE),
enrichment backfill updates, and rich querying by category, language, country, quality, and date range.
"""

from typing import Any, Dict, List, Optional
import hashlib
import json
import logging
from datetime import datetime
from src.database import get_connection

logger = logging.getLogger(__name__)


def generate_article_id(url: str) -> str:
    """
    Generates a deterministic unique ID for an article using SHA-256 hash of its URL.
    """
    if url:
        hash_digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
        return f"news_{hash_digest}"
    return f"news_{int(datetime.utcnow().timestamp())}"


def sanitize_article_dict(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepares and normalizes article values for MySQL insertion.
    Handles missing/empty optional fields and enriched metadata.
    """
    url = (article.get("url") or "").strip()
    title = (article.get("title") or "").strip()
    summary = (article.get("summary") or "").strip() or None
    source = (article.get("source") or "Unknown").strip()
    author = (article.get("author") or "Unknown").strip() or None
    category = (article.get("category") or "World").strip()
    language = (article.get("language") or "English").strip()
    country = (article.get("country") or "Global").strip()
    quality_status = (article.get("quality_status") or "valid").strip()
    article_id = article.get("id") or article.get("article_id") or generate_article_id(url)

    # Clean keywords list to JSON string
    keywords_raw = article.get("keywords")
    if isinstance(keywords_raw, list):
        keywords = json.dumps(keywords_raw, ensure_ascii=False)
    elif isinstance(keywords_raw, str):
        keywords = keywords_raw
    else:
        keywords = "[]"

    # Clean published_at for DATETIME storage (YYYY-MM-DD HH:MM:SS)
    from src.news_processor import parse_published_date
    published_at_raw = article.get("published_at") or article.get("published")
    published_at = parse_published_date(published_at_raw)

    return {
        "article_id": article_id,
        "title": title,
        "summary": summary,
        "url": url,
        "source": source,
        "published_at": published_at,
        "author": author,
        "category": category,
        "language": language,
        "country": country,
        "keywords": keywords,
        "quality_status": quality_status,
        "embedding_status": article.get("embedding_status", "pending"),
    }


def insert_news(article: Dict[str, Any]) -> bool:
    """
    Inserts a single cleaned and enriched article into MySQL.
    Uses INSERT IGNORE to skip duplicate URLs safely.
    Returns True if a new row was inserted, False if skipped as duplicate.
    """
    sanitized = sanitize_article_dict(article)
    if not sanitized["url"] or not sanitized["title"]:
        logger.warning("Attempted to insert invalid article missing title or URL.")
        return False

    query = """
        INSERT IGNORE INTO news (
            article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
    """
    params = (
        sanitized["article_id"],
        sanitized["title"],
        sanitized["summary"],
        sanitized["url"],
        sanitized["source"],
        sanitized["published_at"],
        sanitized["author"],
        sanitized["category"],
        sanitized["language"],
        sanitized["country"],
        sanitized["keywords"],
        sanitized["quality_status"],
    )

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        inserted = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return inserted
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting article '{sanitized.get('title')}': {e}")
        raise
    finally:
        conn.close()


def insert_many_news(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Batch inserts a list of enriched articles into MySQL with duplicate prevention.
    Returns dictionary with counts and list of newly inserted articles:
    {"inserted": X, "skipped": Y, "total": Z, "new_articles": [...]}.
    """
    if not articles:
        return {"inserted": 0, "skipped": 0, "total": 0, "new_articles": []}

    query = """
        INSERT IGNORE INTO news (
            article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status, embedding_status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
    """

    param_list = []
    sanitized_articles = []

    for art in articles:
        sanitized = sanitize_article_dict(art)
        if sanitized["url"] and sanitized["title"]:
            sanitized_articles.append(sanitized)
            param_list.append((
                sanitized["article_id"],
                sanitized["title"],
                sanitized["summary"],
                sanitized["url"],
                sanitized["source"],
                sanitized["published_at"],
                sanitized["author"],
                sanitized["category"],
                sanitized["language"],
                sanitized["country"],
                sanitized["keywords"],
                sanitized["quality_status"],
                sanitized["embedding_status"],
            ))

    if not param_list:
        return {"inserted": 0, "skipped": 0, "total": len(articles), "new_articles": []}

    conn = get_connection()
    inserted_count = 0
    new_articles = []

    try:
        cursor = conn.cursor()
        for idx, params in enumerate(param_list):
            cursor.execute(query, params)
            if cursor.rowcount > 0:
                inserted_count += 1
                new_articles.append(sanitized_articles[idx])
        conn.commit()
        cursor.close()
        skipped_count = len(param_list) - inserted_count
        return {
            "inserted": inserted_count,
            "skipped": skipped_count,
            "total": len(articles),
            "new_articles": new_articles,
        }
    except Exception as e:
        conn.rollback()
        logger.error(f"Error during batch news insertion: {e}")
        raise
    finally:
        conn.close()


def update_embedding_status(article_ids: List[str], status: str = "completed") -> int:
    """
    Updates embedding_status in MySQL for a batch of article_ids after ChromaDB vector indexing.
    """
    if not article_ids:
        return 0

    format_strings = ",".join(["%s"] * len(article_ids))
    query = f"UPDATE news SET embedding_status = %s WHERE article_id IN ({format_strings});"
    params = [status] + list(article_ids)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        updated_count = cursor.rowcount
        conn.commit()
        cursor.close()
        logger.info(f"Updated embedding_status to '{status}' for {updated_count} articles.")
        return updated_count
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating embedding_status: {e}")
        return 0
    finally:
        conn.close()


def get_pending_embedding_articles(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieves articles from MySQL that are marked as 'pending' for embedding generation.
    Enforces eventual consistency if a previous vector DB insertion failed.
    """
    query = """
        SELECT id, article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status, embedding_status
        FROM news
        WHERE embedding_status = 'pending' OR embedding_status IS NULL
        ORDER BY id ASC
        LIMIT %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        result = _rows_to_dicts(cursor, rows)
        cursor.close()
        return result
    except Exception as e:
        logger.error(f"Error fetching pending embedding articles: {e}")
        return []
    finally:
        conn.close()


def update_article_enrichment(article_id: str, enriched_dict: Dict[str, Any]) -> bool:
    """
    Updates an existing MySQL article record with enriched Phase 3 fields.
    Used for safe backfilling of existing database records.
    """
    sanitized = sanitize_article_dict(enriched_dict)
    query = """
        UPDATE news
        SET title = %s,
            summary = %s,
            category = %s,
            language = %s,
            country = %s,
            keywords = %s,
            quality_status = %s
        WHERE article_id = %s;
    """
    params = (
        sanitized["title"],
        sanitized["summary"],
        sanitized["category"],
        sanitized["language"],
        sanitized["country"],
        sanitized["keywords"],
        sanitized["quality_status"],
        article_id,
    )


    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        updated = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return updated
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating enrichment for article {article_id}: {e}")
        return False
    finally:
        conn.close()


def _rows_to_dicts(cursor, rows: List[Any]) -> List[Dict[str, Any]]:
    """
    Helper function to convert raw MySQL/SQLite tuple or dict rows into structured Python dicts.
    """
    if not rows:
        return []

    if isinstance(rows[0], dict):
        return rows

    if not hasattr(cursor, "description") or not cursor.description:
        return []

    colnames = [desc[0] for desc in cursor.description]
    result = []
    for row in rows:
        item = {}
        for col, val in zip(colnames, row):
            if isinstance(val, datetime):
                item[col] = val.strftime("%Y-%m-%d %H:%M:%S")
            else:
                item[col] = val
        result.append(item)
    return result


_LAST_REFRESH_TIMESTAMP: float = 0.0

SEED_ARTICLES = [
    {
        "article_id": "seed_world_01",
        "title": "Global Leaders Convene for Major Sustainable Energy Summit",
        "summary": "International delegates assemble to ratify international transition frameworks for renewable energy and zero-emission grid resilience.",
        "url": "https://www.bbc.com/news/world-energy-summit-2026",
        "source": "BBC World News",
        "published_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "author": "Global News Desk",
        "category": "World",
        "language": "English",
        "country": "Global",
        "keywords": ["energy", "summit", "climate", "renewables", "leaders"],
        "quality_status": "valid",
    },
    {
        "article_id": "seed_tech_02",
        "title": "Next-Generation Multimodal AI Models Redefine Conversational Intelligence",
        "summary": "Breakthrough artificial intelligence frameworks demonstrate real-time reasoning, low-latency multilingual voice comprehension, and automated data grounding.",
        "url": "https://techcrunch.com/2026/multimodal-ai-breakthroughs",
        "source": "TechCrunch",
        "published_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "author": "Tech Analyst",
        "category": "Technology",
        "language": "English",
        "country": "United States",
        "keywords": ["AI", "technology", "multimodal", "intelligence", "models"],
        "quality_status": "valid",
    },
    {
        "article_id": "seed_biz_03",
        "title": "Global Central Banks Report Stable Inflation and Robust Market Growth",
        "summary": "Financial markets respond favorably as quarterly economic reports show sustained trade volumes and tech index gains across global exchanges.",
        "url": "https://www.reuters.com/business/global-markets-inflation-outlook",
        "source": "Reuters",
        "published_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "author": "Markets Desk",
        "category": "Business",
        "language": "English",
        "country": "Global",
        "keywords": ["business", "markets", "economy", "finance", "stocks"],
        "quality_status": "valid",
    },
    {
        "article_id": "seed_india_04",
        "title": "India Expands Digital Infrastructure and Semiconductor Manufacturing Ecosystem",
        "summary": "Government initiatives accelerate high-tech chip fabrication facilities and digital commerce integration across metropolitan hubs.",
        "url": "https://timesofindia.indiatimes.com/india-tech-semiconductor-expansion",
        "source": "Times of India",
        "published_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "author": "National Bureau",
        "category": "Technology",
        "language": "English",
        "country": "India",
        "keywords": ["India", "manufacturing", "semiconductor", "digital", "technology"],
        "quality_status": "valid",
    },
    {
        "article_id": "seed_climate_05",
        "title": "Ocean Conservation Accord Secures Protection for High Seas Biodiversity",
        "summary": "Scientists and environmental agencies welcome landmark maritime protection treaty safeguarding marine wildlife and coral ecosystems.",
        "url": "https://www.aljazeera.com/news/ocean-conservation-accord-biodiversity",
        "source": "Al Jazeera",
        "published_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "author": "Environment Desk",
        "category": "Climate",
        "language": "English",
        "country": "Global",
        "keywords": ["ocean", "climate", "environment", "conservation", "wildlife"],
        "quality_status": "valid",
    },
]


def ensure_seed_news_loaded() -> None:
    """Inserts initial seed news articles if the news database table is empty."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM news;")
        row = cur.fetchone()
        count = row["count"] if isinstance(row, dict) else (row[0] if row else 0)
        cur.close()
        conn.close()

        if count == 0:
            logger.info("Database empty on cold start. Inserting pre-seeded news articles...")
            insert_many_news(SEED_ARTICLES)
    except Exception as err:
        logger.warning(f"Could not load seed news: {err}")


def refresh_live_news(max_feeds: Optional[int] = None, fast_mode: bool = True) -> List[Dict[str, Any]]:
    """
    Fetches real-time breaking news from active RSS feeds concurrently,
    cleans, enriches, deduplicates, and saves to database for fresh live updates.
    """
    global _LAST_REFRESH_TIMESTAMP
    import time
    _LAST_REFRESH_TIMESTAMP = time.time()

    try:
        from config.feeds import RSS_FEEDS
        from src.rss_collector import collect_all_feeds
        from src.cleaner import deduplicate_articles
        from src.news_processor import process_article

        target_feeds = RSS_FEEDS
        # In fast_mode or on-demand serverless requests, only query top tier fast feeds
        if fast_mode:
            target_feeds = {
                "world": RSS_FEEDS.get("world", [])[:2],
                "technology": RSS_FEEDS.get("technology", [])[:2],
            }
        elif max_feeds and isinstance(target_feeds, dict):
            target_feeds = {k: v for i, (k, v) in enumerate(RSS_FEEDS.items()) if i < max_feeds}

        raw_articles = collect_all_feeds(target_feeds, max_workers=6, timeout_seconds=3.0)
        if not raw_articles:
            return []

        processed = []
        for art in raw_articles:
            p_art, _ = process_article(art)
            if p_art:
                processed.append(p_art)

        unique_arts = deduplicate_articles(processed)
        if unique_arts:
            insert_many_news(unique_arts)
            try:
                from src.vector_store import add_or_update_articles
                add_or_update_articles(unique_arts[:25])
            except Exception:
                pass
        return unique_arts
    except Exception as err:
        logger.error(f"Error refreshing live news: {err}")
        return []


def get_latest_news(limit: int = 10, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieves the most recent news articles strictly sorted by publication time.
    Guarantees instant response using seed data and non-blocking RSS refreshes.
    """
    import time
    query = """
        SELECT id, article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status, created_at, updated_at
        FROM news
        WHERE published_at IS NOT NULL
        ORDER BY published_at DESC
        LIMIT %s;
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (max(limit * 2, 20),))
        rows = cursor.fetchall()
        result = _rows_to_dicts(cursor, rows)
        cursor.close()
        conn.close()

        # If DB is completely empty (e.g. cold start), load seed articles instantly
        if not result:
            ensure_seed_news_loaded()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            result = _rows_to_dicts(cursor, rows)
            cursor.close()
            conn.close()

        # Check if live RSS refresh should run with cooldown protection (at least 3 mins between refreshes)
        now_ts = time.time()
        cooldown_passed = (now_ts - _LAST_REFRESH_TIMESTAMP) > 180
        needs_refresh = (force_refresh or len(result) < 3) and cooldown_passed

        if needs_refresh:
            logger.info("Database news needs refresh and cooldown passed. Fast-refreshing live feeds...")
            refresh_live_news(fast_mode=True)
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            result = _rows_to_dicts(cursor, rows)
            cursor.close()
            conn.close()

        return result[:limit] if result else []
    except Exception as err:
        logger.error(f"Error in get_latest_news: {err}")
        return SEED_ARTICLES[:limit]


def get_news_by_category(category: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieves latest news articles matching a specific category taxonomy.
    """
    query = """
        SELECT id, article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status, created_at, updated_at
        FROM news
        WHERE LOWER(category) = LOWER(%s)
        ORDER BY COALESCE(published_at, created_at) DESC
        LIMIT %s;
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (category.strip(), limit))
        rows = cursor.fetchall()
        result = _rows_to_dicts(cursor, rows)
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        logger.error(f"MySQL error in get_news_by_category: {e}")
        return get_latest_news(limit=limit)



def get_news_by_source(source: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieves latest news articles matching a specific source publisher (e.g. 'BBC News').
    """
    query = """
        SELECT id, article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status, created_at, updated_at
        FROM news
        WHERE LOWER(source) = LOWER(%s)
        ORDER BY COALESCE(published_at, created_at) DESC
        LIMIT %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, (source.strip(), limit))
        rows = cursor.fetchall()
        result = _rows_to_dicts(cursor, rows)
        cursor.close()
        return result
    finally:
        conn.close()


def get_news_by_language(language: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieves latest news articles matching a specific language (e.g. 'English').
    """
    query = """
        SELECT id, article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status, created_at, updated_at
        FROM news
        WHERE LOWER(language) = LOWER(%s)
        ORDER BY COALESCE(published_at, created_at) DESC
        LIMIT %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, (language.strip(), limit))
        rows = cursor.fetchall()
        result = _rows_to_dicts(cursor, rows)
        cursor.close()
        return result
    finally:
        conn.close()



def get_news_by_country(country: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieves latest news articles matching a specific country.
    """
    query = """
        SELECT id, article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status, created_at, updated_at
        FROM news
        WHERE LOWER(country) = LOWER(%s)
        ORDER BY COALESCE(published_at, created_at) DESC
        LIMIT %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, (country.strip(), limit))
        rows = cursor.fetchall()
        result = _rows_to_dicts(cursor, rows)
        cursor.close()
        return result
    finally:
        conn.close()


def get_news_by_quality(quality_status: str = "valid", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieves news articles filtered by quality status ('valid', 'needs_review', 'invalid').
    """
    query = """
        SELECT id, article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status, created_at, updated_at
        FROM news
        WHERE quality_status = %s
        ORDER BY COALESCE(published_at, created_at) DESC
        LIMIT %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, (quality_status.strip(), limit))
        rows = cursor.fetchall()
        result = _rows_to_dicts(cursor, rows)
        cursor.close()
        return result
    finally:
        conn.close()


def get_today_news(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves news articles published or ingested today.
    """
    query = """
        SELECT id, article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status, created_at, updated_at
        FROM news
        WHERE DATE(COALESCE(published_at, created_at)) = CURDATE()
        ORDER BY COALESCE(published_at, created_at) DESC
        LIMIT %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        result = _rows_to_dicts(cursor, rows)
        cursor.close()
        return result
    finally:
        conn.close()


def get_recent_news(hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves news articles published or ingested within the past N hours.
    """
    query = """
        SELECT id, article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status, created_at, updated_at
        FROM news
        WHERE COALESCE(published_at, created_at) >= NOW() - INTERVAL %s HOUR
        ORDER BY COALESCE(published_at, created_at) DESC
        LIMIT %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, (hours, limit))
        rows = cursor.fetchall()
        result = _rows_to_dicts(cursor, rows)
        cursor.close()
        return result
    finally:
        conn.close()

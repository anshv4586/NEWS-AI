"""
Integrated Retriever Module for Global News AI - Phase 5

Combines ChromaDB vector similarity search with MySQL relational lookup,
enforcing configurable similarity score thresholds (min_score=0.35) and Top-K filtering.
"""

from typing import Any, Dict, List, Optional
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.vector_store import search_similar_articles
from src.news_repository import get_connection, _rows_to_dicts

logger = logging.getLogger(__name__)

# Load configuration defaults from .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", 5))
DEFAULT_SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.35))


def get_full_articles_by_ids(article_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetches full article metadata records from MySQL database for a list of article_ids.
    Returns dictionary mapping article_id -> article_dict.
    """
    if not article_ids:
        return {}

    format_strings = ",".join(["%s"] * len(article_ids))
    query = f"""
        SELECT id, article_id, title, summary, url, source, published_at, author, category, language, country, keywords, quality_status, created_at, updated_at
        FROM news
        WHERE article_id IN ({format_strings});
    """

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, tuple(article_ids))
        rows = cursor.fetchall()
        dict_rows = _rows_to_dicts(cursor, rows)
        cursor.close()
        return {row["article_id"]: row for row in dict_rows}
    except Exception as e:
        logger.error(f"Error fetching full articles from MySQL: {e}")
        return {}
    finally:
        conn.close()


def retrieve_context_articles(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_SIMILARITY_THRESHOLD,
    filter_dict: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Performs hybrid retrieval:
    1. Vector similarity search in ChromaDB.
    2. Filters vector hits below min_score threshold.
    3. Fetches complete metadata records from MySQL database.
    4. Merges similarity scores and returns ordered list of relevant articles.
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    logger.info(f"Retrieving top {top_k} vector hits for query: '{cleaned_query}' (min_score: {min_score})...")
    vector_results = search_similar_articles(cleaned_query, top_k=top_k, filter_dict=filter_dict)

    if not vector_results:
        logger.info("ChromaDB returned 0 vector matches.")
        return []

    # Step 2: Threshold Filtering
    filtered_hits = [hit for hit in vector_results if hit["similarity_score"] >= min_score]
    logger.info(f"Vector search returned {len(vector_results)} hits -> {len(filtered_hits)} above threshold ({min_score}).")

    if not filtered_hits:
        logger.info("No vector search hits satisfied the minimum similarity score threshold.")
        return []

    # Step 3: Fetch full article records from MySQL database
    article_ids = [hit["article_id"] for hit in filtered_hits]
    mysql_articles = get_full_articles_by_ids(article_ids)

    # Step 4: Merge vector metadata & score with MySQL full record
    retrieved_articles = []
    for rank, hit in enumerate(filtered_hits, start=1):
        art_id = hit["article_id"]
        mysql_record = mysql_articles.get(art_id, {})

        title = mysql_record.get("title") or hit.get("title", "")
        summary = mysql_record.get("summary") or hit.get("snippet", "")
        source = mysql_record.get("source") or hit.get("source", "Unknown")
        url = mysql_record.get("url") or hit.get("url", "")
        published_at = mysql_record.get("published_at") or hit.get("published_at", "")
        category = mysql_record.get("category") or hit.get("category", "World")
        language = mysql_record.get("language") or hit.get("language", "English")
        country = mysql_record.get("country") or hit.get("country", "Global")

        merged = {
            "rank": rank,
            "article_id": art_id,
            "similarity_score": hit["similarity_score"],
            "title": title,
            "summary": summary,
            "source": source,
            "url": url,
            "published_at": str(published_at),
            "category": category,
            "language": language,
            "country": country,
        }
        retrieved_articles.append(merged)

    return retrieved_articles

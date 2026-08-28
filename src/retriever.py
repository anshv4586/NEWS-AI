"""
Integrated Retriever Module for Global News AI - Phase 5

Combines ChromaDB vector similarity search with MySQL relational lookup,
enforcing configurable similarity score thresholds (min_score=0.35) and Top-K filtering.
"""

from typing import Any, Dict, List, Optional
import os
import math
import logging
from datetime import datetime, timezone
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

# Default ranking weight parameters
DEFAULT_WEIGHT_VECTOR = float(os.getenv("WEIGHT_VECTOR", 0.7))
DEFAULT_WEIGHT_RECENCY = float(os.getenv("WEIGHT_RECENCY", 0.3))



def parse_datetime(dt_str: Any) -> Optional[datetime]:
    """Parses datetime strings into datetime objects."""
    if not dt_str:
        return None
    dt_str = str(dt_str).strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str.split(".")[0], fmt)
        except ValueError:
            continue
    return None


def calculate_recency_score(published_at_str: Any, reference_dt: Optional[datetime] = None) -> float:
    """
    Computes a recency score between 0.0 and 1.0 using exponential time decay.
    Score = 1.0 for brand new news, decaying smoothly with age in hours.
    """
    dt = parse_datetime(published_at_str)
    if not dt:
        return 0.5  # Neutral default score for missing timestamp

    ref = reference_dt or datetime.now()
    age_hours = max(0.0, (ref - dt).total_seconds() / 3600.0)

    # Exponential decay half-life of 48 hours
    decay_rate = math.log(2) / 48.0
    recency_score = math.exp(-decay_rate * age_hours)
    return round(max(0.0, min(1.0, recency_score)), 4)


def build_chroma_filter(
    country: Optional[str] = None,
    category: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Builds ChromaDB 'where' filter dictionary supporting single and combined filters.
    """
    conditions = []
    if country and country != "Global":
        conditions.append({"country": country})
    if category and category != "World":
        conditions.append({"category": category})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


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
    country: Optional[str] = None,
    category: Optional[str] = None,
    time_range: str = "all",
    w_vector: float = DEFAULT_WEIGHT_VECTOR,
    w_recency: float = DEFAULT_WEIGHT_RECENCY,
    filter_dict: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Performs hybrid retrieval with metadata filtering & recency ranking:
    1. Builds metadata filters (country, category) for ChromaDB vector search.
    2. Retrieves candidate matches from ChromaDB.
    3. Fetches full metadata records from MySQL database.
    4. Calculates recency decay score for each article.
    5. Computes hybrid Final Score = (w_vector * semantic_score) + (w_recency * recency_score).
    6. Returns top_k ranked articles.
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    # Step 1: Construct ChromaDB metadata filter if not provided explicitly
    if not filter_dict:
        filter_dict = build_chroma_filter(country=country, category=category)

    logger.info(
        f"Retrieving candidate vectors for query: '{cleaned_query}' | Filter: {filter_dict} | "
        f"Top-K: {top_k} | min_score: {min_score}..."
    )

    # Fetch broader candidate pool (top_k * 3) for re-ranking
    candidate_k = max(top_k * 3, 15)
    vector_results = search_similar_articles(cleaned_query, top_k=candidate_k, filter_dict=filter_dict)

    # Fallback to unfiltered vector search if filtered search yields 0 hits
    if not vector_results and filter_dict:
        logger.info("Filtered ChromaDB search returned 0 hits. Falling back to unfiltered vector search...")
        vector_results = search_similar_articles(cleaned_query, top_k=candidate_k, filter_dict=None)

    if not vector_results:
        logger.info("ChromaDB returned 0 vector matches.")
        return []

    # Step 2: Minimum similarity threshold filtering
    filtered_hits = [hit for hit in vector_results if hit["similarity_score"] >= min_score]
    logger.info(f"Vector search: {len(vector_results)} candidate hits -> {len(filtered_hits)} above threshold ({min_score}).")

    if not filtered_hits:
        # Fallback to taking top candidates even if slightly below strict threshold
        filtered_hits = vector_results[:top_k]

    # Step 3: Fetch full article records from MySQL database
    article_ids = [hit["article_id"] for hit in filtered_hits]
    mysql_articles = get_full_articles_by_ids(article_ids)

    # Step 4: Hybrid Recency + Semantic Re-ranking
    scored_articles = []
    for hit in filtered_hits:
        art_id = hit["article_id"]
        mysql_record = mysql_articles.get(art_id, {})

        title = mysql_record.get("title") or hit.get("title", "")
        summary = mysql_record.get("summary") or hit.get("snippet", "")
        source = mysql_record.get("source") or hit.get("source", "Unknown")
        url = mysql_record.get("url") or hit.get("url", "")
        published_at = mysql_record.get("published_at") or hit.get("published_at", "")
        art_category = mysql_record.get("category") or hit.get("category", "World")
        art_language = mysql_record.get("language") or hit.get("language", "English")
        art_country = mysql_record.get("country") or hit.get("country", "Global")

        sem_score = hit["similarity_score"]
        rec_score = calculate_recency_score(published_at)
        final_score = round((w_vector * sem_score) + (w_recency * rec_score), 4)

        merged = {
            "article_id": art_id,
            "final_score": final_score,
            "similarity_score": sem_score,
            "recency_score": rec_score,
            "title": title,
            "summary": summary,
            "source": source,
            "url": url,
            "published_at": str(published_at),
            "category": art_category,
            "language": art_language,
            "country": art_country,
        }
        scored_articles.append(merged)

    # Sort articles by hybrid final_score in descending order
    scored_articles.sort(key=lambda x: x["final_score"], reverse=True)

    # Re-assign 1-based rank to top_k results
    top_results = scored_articles[:top_k]
    for rank, art in enumerate(top_results, start=1):
        art["rank"] = rank

    logger.info(f"Successfully retrieved and re-ranked top {len(top_results)} articles.")
    return top_results


if __name__ == "__main__":
    import sys
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    logging.basicConfig(level=logging.INFO)
    print("\n--- RETRIEVER RECENCY & FILTERING DEMO ---")
    demo_articles = retrieve_context_articles(
        query="AI regulation in India",
        country="India",
        category="Technology",
        top_k=3,
    )
    for art in demo_articles:
        print(f"Rank {art['rank']} | Final Score: {art['final_score']} (Vector: {art['similarity_score']}, Recency: {art['recency_score']})")
        print(f"Title : {art['title']}")
        print(f"Source: {art['source']} | Country: {art['country']} | Date: {art['published_at']}\n")


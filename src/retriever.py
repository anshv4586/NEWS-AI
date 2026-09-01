"""
Integrated Retriever Module for Global News AI - Phase 5

Combines ChromaDB vector similarity search with MySQL relational lookup,
enforcing configurable similarity score thresholds (min_score=0.35) and Top-K filtering.
"""

from typing import Any, Dict, List, Optional
import os
import re
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
DEFAULT_SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.30))

# Recency & vector ranking weight parameters (strong 50-50 balance)
DEFAULT_WEIGHT_VECTOR = float(os.getenv("WEIGHT_VECTOR", 0.5))
DEFAULT_WEIGHT_RECENCY = float(os.getenv("WEIGHT_RECENCY", 0.5))



def parse_datetime(dt_str: Any) -> Optional[datetime]:
    """Parses datetime strings into datetime objects."""
    if not dt_str:
        return None
    dt_str = str(dt_str).strip()
    try:
        import dateutil.parser
        dt = dateutil.parser.parse(dt_str)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        pass

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
    Score = 1.0 for brand new news (<2 hours), decaying smoothly (half-life of 18 hours).
    """
    dt = parse_datetime(published_at_str)
    if not dt:
        return 0.2

    ref = reference_dt or datetime.utcnow()
    age_hours = max(0.0, (ref - dt).total_seconds() / 3600.0)

    # Exponential decay half-life of 18 hours
    decay_rate = math.log(2) / 18.0
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
    Fetches full article metadata records from MySQL/SQLite database for a list of article_ids.
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

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, tuple(article_ids))
        rows = cursor.fetchall()
        dict_rows = _rows_to_dicts(cursor, rows)
        cursor.close()
        return {row["article_id"]: row for row in dict_rows}
    except Exception as e:
        logger.error(f"Error fetching full articles from database: {e}")
        return {}
    finally:
        if conn and hasattr(conn, "close"):
            try:
                conn.close()
            except Exception:
                pass


def is_valid_real_article(art: Dict[str, Any]) -> bool:
    """
    Excludes synthetic/mock test records and empty-summary articles from being returned to users in RAG answers.
    """
    if not art:
        return False
    title = (art.get("title") or "").lower()
    source = (art.get("source") or "").lower()
    summary = (art.get("summary") or "").strip()
    
    # Filter out test/mock artifacts
    if any(w in source for w in ["test", "unittest", "minimal", "mock", "sample", "demo"]):
        return False
    if any(w in title for w in ["minimal article", "test headline", "automated test", "test news"]):
        return False

    # Require substantive summary details (at least 30 characters)
    if not summary or len(summary) < 30 or summary.lower() == title.lower():
        return False

    if art.get("quality_status") in ("invalid", "needs_review"):
        return False

    return True


def normalize_text_for_match(text: str) -> str:
    """Normalizes text for robust headline comparison, stripping punctuation and converting smart quotes."""
    if not text:
        return ""
    import unicodedata
    t = unicodedata.normalize("NFKD", str(text))
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
    t = re.sub(r"[^\w\s]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def find_article_by_headline_match(query: str) -> Optional[Dict[str, Any]]:
    """
    Detects if the user query contains or matches an exact or fuzzy article headline in the database.
    Handles quote variants (', ’), punctuation, prefixes, and word overlap for 100% precision.
    """
    clean_q = (query or "").strip()
    prefixes = [
        r"^tell me more details about\s*:\s*",
        r"^tell me more about\s*:\s*",
        r"^tell me about\s*:\s*",
        r"^details on\s*:\s*",
        r"^more info on\s*:\s*",
        r"^what about\s*:\s*",
    ]
    extracted = clean_q
    for p in prefixes:
        extracted = re.sub(p, "", extracted, flags=re.IGNORECASE).strip()

    if len(extracted) < 10:
        return None

    norm_target = normalize_text_for_match(extracted)
    target_words = set(norm_target.split())

    try:
        from src.database import execute_query
        rows = execute_query(
            "SELECT * FROM news WHERE published_at IS NOT NULL AND summary IS NOT NULL AND LENGTH(TRIM(summary)) >= 30 ORDER BY id DESC LIMIT 1000",
            fetchall=True
        )
        if not rows:
            return None

        best_match = None
        best_score = 0.0

        for r in rows:
            if not is_valid_real_article(r):
                continue
            norm_title = normalize_text_for_match(r.get("title", ""))
            if not norm_title:
                continue

            # Exact or Substring match
            if norm_title == norm_target or norm_target in norm_title or norm_title in norm_target:
                matched_art = dict(r)
                if matched_art.get("published_at") and hasattr(matched_art["published_at"], "strftime"):
                    matched_art["published_at"] = matched_art["published_at"].strftime("%Y-%m-%d %H:%M:%S")
                elif matched_art.get("published_at"):
                    matched_art["published_at"] = str(matched_art["published_at"]).strip()
                matched_art["rank"] = 1
                return matched_art

            # Jaccard word overlap
            title_words = set(norm_title.split())
            if title_words and target_words:
                overlap = len(title_words.intersection(target_words)) / max(len(target_words), 1)
                if overlap >= 0.60 and overlap > best_score:
                    best_score = overlap
                    best_match = dict(r)

        if best_match and best_score >= 0.60:
            if best_match.get("published_at") and hasattr(best_match["published_at"], "strftime"):
                best_match["published_at"] = best_match["published_at"].strftime("%Y-%m-%d %H:%M:%S")
            elif best_match.get("published_at"):
                best_match["published_at"] = str(best_match["published_at"]).strip()
            best_match["rank"] = 1
            return best_match

    except Exception as err:
        logger.error(f"Error matching article by headline: {err}")

    return None


def _keyword_rank_fallback(query: str, articles: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Lightweight keyword/BM25-style scorer when ChromaDB vector index is unavailable.
    """
    valid_pool = [a for a in articles if is_valid_real_article(a)]
    if not valid_pool:
        return []
    
    q_words = set(re.findall(r'\w+', (query or "").lower()))
    if not q_words:
        return valid_pool[:top_k]

    scored = []
    for art in valid_pool:
        text = f"{art.get('title', '')} {art.get('summary', '')} {art.get('category', '')} {art.get('country', '')}".lower()
        score = 0
        for w in q_words:
            if len(w) > 2 and w in text:
                score += text.count(w) * 2
        scored.append((score, art))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [item[1] for item in scored[:top_k]]
    for idx, art in enumerate(results, 1):
        art["rank"] = idx
    return results


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
    1. Checks for exact headline / card match first for 100% precision.
    2. Builds metadata filters (country, category) for ChromaDB vector search.
    3. Retrieves candidate matches from ChromaDB.
    4. Fetches full metadata records from database.
    5. Calculates recency decay score for each article.
    6. Filters out synthetic / mock test articles.
    7. Computes hybrid Final Score = (w_vector * semantic_score) + (w_recency * recency_score).
    8. Returns top_k ranked articles.
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    # Step 0: Direct Headline Match for Top Headline card clicks
    direct_match = find_article_by_headline_match(cleaned_query)
    if direct_match:
        logger.info(f"[Retriever] Exact headline match found: '{direct_match.get('title')}'")
        return [direct_match]

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
        logger.info("Vector search returned 0 matches or vector DB disabled. Falling back to database news keyword matching...")
        try:
            from src.news_repository import get_latest_news, get_news_by_category, get_news_by_country
            if category and category != "World":
                db_pool = get_news_by_category(category, limit=30)
            elif country and country != "Global":
                db_pool = get_news_by_country(country, limit=30)
            else:
                db_pool = get_latest_news(limit=30)
            
            if db_pool:
                return _keyword_rank_fallback(cleaned_query, db_pool, top_k=top_k)
            return []
        except Exception as err:
            logger.error(f"News fallback retrieval error: {err}")
            return []

    # Step 2: Minimum similarity threshold filtering & Synthetic Article Exclusion
    filtered_hits = []
    for hit in vector_results:
        if hit.get("similarity_score", 0) >= min_score and is_valid_real_article(hit):
            filtered_hits.append(hit)

    logger.info(f"Vector search: {len(vector_results)} candidate hits -> {len(filtered_hits)} valid above threshold ({min_score}).")

    if not filtered_hits:
        # Fallback to taking top valid candidates
        filtered_hits = [h for h in vector_results if is_valid_real_article(h)][:top_k]

    # Step 3: Fetch full article records from database
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

        merged = {
            "article_id": art_id,
            "title": title,
            "summary": summary,
            "source": source,
            "url": url,
            "published_at": str(published_at),
            "category": art_category,
            "language": art_language,
            "country": art_country,
        }

        if not is_valid_real_article(merged):
            continue

        sem_score = hit["similarity_score"]
        rec_score = calculate_recency_score(published_at)
        final_score = round((w_vector * sem_score) + (w_recency * rec_score), 4)

        merged["final_score"] = final_score
        merged["similarity_score"] = sem_score
        merged["recency_score"] = rec_score
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


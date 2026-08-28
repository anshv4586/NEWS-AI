"""
Vector Database Module for Global News AI - Phase 4

Provides a clean interface to local persistent ChromaDB vector store.
Handles collection management, duplicate-safe upsert indexing,
Cosine Similarity search, and metadata filtering.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import logging
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except Exception:
    chromadb = None
    Settings = None
    HAS_CHROMADB = False

from src.embeddings import (
    create_embedding,
    create_embeddings_batch,
    prepare_embedding_text,
    EMBEDDING_DIMENSION,
)

logger = logging.getLogger(__name__)

# Constants
VECTOR_DB_DIR = Path(__file__).resolve().parent.parent / "vector_db"
COLLECTION_NAME = "news_vectors"

# Cached ChromaDB client & collection instances
_CLIENT_INSTANCE: Optional[Any] = None
_COLLECTION_INSTANCE: Optional[Any] = None


def get_vector_client() -> Any:
    """
    Initializes and returns a persistent ChromaDB client instance stored in vector_db/.
    """
    global _CLIENT_INSTANCE
    if not HAS_CHROMADB or chromadb is None:
        logger.warning("ChromaDB library not installed. Vector store disabled.")
        return None

    if _CLIENT_INSTANCE is None:
        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing ChromaDB PersistentClient at '{VECTOR_DB_DIR}'...")
        _CLIENT_INSTANCE = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    return _CLIENT_INSTANCE


def get_vector_collection() -> Any:
    """
    Retrieves or creates the 'news_vectors' ChromaDB collection using Cosine Similarity.
    """
    global _COLLECTION_INSTANCE
    if not HAS_CHROMADB or chromadb is None:
        return None

    if _COLLECTION_INSTANCE is None:
        client = get_vector_client()
        if not client:
            return None
        logger.info(f"Getting or creating ChromaDB collection '{COLLECTION_NAME}' (Cosine Metric)...")
        _COLLECTION_INSTANCE = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _COLLECTION_INSTANCE



def add_or_update_articles(articles: List[Dict[str, Any]]) -> int:
    """
    Upserts (inserts or updates) a list of articles into ChromaDB.
    Guarantees idempotency — running multiple times will update existing vector IDs
    rather than creating duplicate entries.
    
    Returns the number of articles upserted.
    """
    if not articles:
        return 0

    collection = get_vector_collection()
    if not collection:
        return 0
    
    ids = []
    documents = []
    metadatas = []
    valid_articles = []

    for art in articles:
        art_id = str(art.get("article_id") or art.get("id") or "")
        url = (art.get("url") or "").strip()
        title = (art.get("title") or "").strip()
        
        if not art_id or not url or not title:
            continue

        embedding_text = prepare_embedding_text(art)
        
        # Prepare metadata dictionary (ChromaDB handles primitive types)
        metadata = {
            "article_id": art_id,
            "title": title[:200],
            "source": (art.get("source") or "Unknown").strip(),
            "url": url[:500],
            "category": (art.get("category") or "World").strip(),
            "language": (art.get("language") or "English").strip(),
            "country": (art.get("country") or "Global").strip(),
            "quality_status": (art.get("quality_status") or "valid").strip(),
            "published_at": str(art.get("published_at") or ""),
        }

        ids.append(art_id)
        documents.append(embedding_text)
        metadatas.append(metadata)
        valid_articles.append(art)

    if not ids:
        return 0

    # Generate 384-dimensional vector embeddings in batch
    embeddings = create_embeddings_batch(documents)

    # Upsert into ChromaDB (duplicate-safe)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    logger.info(f"Upserted {len(ids)} vector documents into ChromaDB collection '{COLLECTION_NAME}'.")
    return len(ids)


def search_similar_articles(
    query: str,
    top_k: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Performs semantic vector similarity search for a text query.
    Optionally applies metadata filters (e.g. filter_dict={"category": "Technology"}).
    
    Returns ranked list of dictionaries containing article_id, similarity_score, metadata, and snippet.
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    collection = get_vector_collection()
    if not collection:
        return []

    query_vector = create_embedding(cleaned_query)

    # Query ChromaDB collection
    query_args = {
        "query_embeddings": [query_vector],
        "n_results": min(top_k, max(1, collection.count())),
    }
    
    if filter_dict:
        query_args["where"] = filter_dict

    try:
        results = collection.query(**query_args)
    except Exception as e:
        logger.error(f"ChromaDB query error: {e}")
        return []

    if not results or not results.get("ids") or not results["ids"][0]:
        return []

    ranked_results = []
    ids_list = results["ids"][0]
    distances_list = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids_list)
    metadatas_list = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else [{}] * len(ids_list)
    documents_list = results["documents"][0] if "documents" in results and results["documents"] else [""] * len(ids_list)

    for art_id, dist, meta, doc in zip(ids_list, distances_list, metadatas_list, documents_list):
        # Convert Cosine Distance to Cosine Similarity score (range 0.0 to 1.0)
        similarity_score = max(0.0, round(1.0 - float(dist), 4))
        
        ranked_results.append({
            "article_id": art_id,
            "similarity_score": similarity_score,
            "title": meta.get("title", ""),
            "source": meta.get("source", ""),
            "url": meta.get("url", ""),
            "category": meta.get("category", ""),
            "language": meta.get("language", ""),
            "country": meta.get("country", ""),
            "published_at": meta.get("published_at", ""),
            "snippet": doc[:250] + "..." if len(doc) > 250 else doc,
            "metadata": meta,
        })

    return ranked_results


def count_vectors() -> int:
    """
    Returns total count of indexed vector documents in ChromaDB.
    """
    collection = get_vector_collection()
    if not collection:
        return 0
    return collection.count()


"""
Build Vector Index Script for Global News AI - Phase 4

Fetches valid processed articles from MySQL database, generates 384-dimensional
vector embeddings using Multilingual SentenceTransformers, and stores/upserts them
into ChromaDB local persistent vector store.

Run executable with:
    python scripts/build_vector_index.py
"""

import logging
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.database import test_connection, get_connection
from src.embeddings import get_embedding_model
from src.news_repository import get_latest_news
from src.vector_store import add_or_update_articles, count_vectors, get_vector_collection

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def build_vector_index() -> int:
    """
    Executes vector embedding generation and indexing pipeline.
    """
    logger.info("Starting Phase 4 Vector Database Indexing Pipeline...")

    # Step 1: Verify MySQL Database Access
    if not test_connection():
        logger.error("MySQL connection failed. Vector indexing aborted.")
        return 1

    # Step 2: Load Multilingual SentenceTransformers Model
    logger.info("Loading Multilingual SentenceTransformer Embedding Model...")
    get_embedding_model()

    # Step 3: Fetch Processed Articles from MySQL
    logger.info("Fetching articles from MySQL database...")
    articles = get_latest_news(limit=1000)
    logger.info(f"Retrieved {len(articles)} articles from MySQL database.")

    if not articles:
        logger.warning("No articles found in MySQL. Indexing complete with 0 items.")
        return 0

    # Step 4: Generate Embeddings & Upsert into ChromaDB
    logger.info("Generating 384-dimensional vector embeddings and indexing into ChromaDB...")
    upserted_count = add_or_update_articles(articles)

    total_vectors = count_vectors()

    print("\n" + "=" * 78)
    print(" PHASE 4 VECTOR INDEXING COMPLETE")
    print("=" * 78)
    print(f" Articles Retrieved from MySQL : {len(articles)}")
    print(f" Vector Documents Upserted     : {upserted_count}")
    print(f" Total Vectors in ChromaDB     : {total_vectors}")
    print("=" * 78 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(build_vector_index())

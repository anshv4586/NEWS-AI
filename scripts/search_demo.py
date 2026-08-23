"""
Semantic Search & Retrieval Demonstration Script for Global News AI - Phase 4

Demonstrates cross-lingual semantic vector search in English, Hindi, Hinglish,
and metadata filtering, linking vector search results back to MySQL database records.

Run executable with:
    python scripts/search_demo.py
"""

import logging
import sys
from pathlib import Path

# Configure UTF-8 encoding for Windows terminal stdout/stderr
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.vector_store import search_similar_articles, count_vectors
from src.news_repository import get_latest_news

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def run_demo():
    """
    Executes sample semantic search queries.
    """
    logger.info(f"Total vector documents in ChromaDB store: {count_vectors()}")

    sample_queries = [
        {"query": "What is happening with artificial intelligence technology policy?", "lang": "English"},
        {"query": "कृत्रिम बुद्धिमत्ता के क्षेत्र में क्या हो रहा है?", "lang": "Hindi"},
        {"query": "AI ke field mein abhi kya news hai?", "lang": "Hinglish"},
        {"query": "US Canada trade tariffs impact on economy", "lang": "News Query"},
    ]

    for q in sample_queries:
        query_text = q["query"]
        lang_label = q["lang"]
        print("\n" + "=" * 80)
        print(f" SEMANTIC SEARCH QUERY ({lang_label.upper()}): \"{query_text}\"")
        print("=" * 80)

        results = search_similar_articles(query_text, top_k=3)
        if not results:
            print(" No results found.")
            continue

        for i, res in enumerate(results, 1):
            print(f" {i}. Score: {res['similarity_score']} | [{res['source']}] ({res['category'].upper()}) - Country: {res['country']}")
            print(f"    Title: {res['title']}")
            print(f"    URL:   {res['url']}")
            print(f"    ID:    {res['article_id']}")
            print("-" * 80)


if __name__ == "__main__":
    run_demo()

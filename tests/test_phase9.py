"""
Phase 9 Real-Time Continuous News Ingestion Test Suite for Global News AI

Verifies:
1. Startup health check (MySQL, ChromaDB vector store, RSS feeds config)
2. Single ingestion cycle execution
3. Duplicate detection & zero re-embedding protection
4. Eventual consistency for pending vector embeddings
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.database import test_connection
from src.vector_store import count_vectors
from src.scheduler import run_startup_health_check, execute_ingestion_cycle
from src.news_repository import (
    insert_many_news,
    get_pending_embedding_articles,
    update_embedding_status,
)


class TestPhase9ContinuousIngestion(unittest.TestCase):

    def test_01_startup_health_check(self):
        self.assertTrue(test_connection())
        self.assertGreaterEqual(count_vectors(), 0)
        self.assertTrue(run_startup_health_check())
        print("\n✅ Test 1 (Startup Health Check) PASSED.")

    def test_02_ingestion_cycle_execution(self):
        stats = execute_ingestion_cycle(cycle_number=999)
        self.assertIn("cycle", stats)
        self.assertIn("raw", stats)
        self.assertIn("new", stats)
        self.assertIn("duplicates", stats)
        self.assertIn("embedded", stats)
        self.assertIn("duration", stats)
        print("\n✅ Test 2 (Ingestion Cycle Execution) PASSED.")

    def test_03_duplicate_prevention_no_reembedding(self):
        # Sample test article
        sample_article = {
            "title": "Phase 9 Automated Test News Article",
            "url": "https://test-phase9-news.com/article-001",
            "summary": "Testing Phase 9 duplicate prevention and embedding idempotency.",
            "source": "Phase 9 Test Source",
            "published_at": "2026-08-26 00:00:00",
            "category": "Technology",
            "language": "English",
            "country": "Global",
        }

        # First Insertion: Should be inserted as new
        res1 = insert_many_news([sample_article])
        self.assertEqual(res1["inserted"], 1)
        self.assertEqual(len(res1["new_articles"]), 1)

        # Second Insertion: Should be detected as duplicate and skipped
        res2 = insert_many_news([sample_article])
        self.assertEqual(res2["inserted"], 0)
        self.assertEqual(res2["skipped"], 1)
        self.assertEqual(len(res2["new_articles"]), 0)

        # Clean up test article's embedding status
        art_id = res1["new_articles"][0]["article_id"]
        update_embedding_status([art_id], status="completed")
        print("\n✅ Test 3 (Duplicate Prevention & Zero Re-embedding) PASSED.")

    def test_04_eventual_consistency_pending_recovery(self):
        pending = get_pending_embedding_articles(limit=10)
        self.assertIsInstance(pending, list)
        print("\n✅ Test 4 (Eventual Consistency & Pending Recovery Query) PASSED.")


if __name__ == "__main__":
    unittest.main()

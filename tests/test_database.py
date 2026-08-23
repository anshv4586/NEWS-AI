"""
Unit and Integration Tests for MySQL News Repository
"""

import unittest
from datetime import datetime
from src.database import test_connection, get_connection
from src.news_repository import (
    insert_news,
    insert_many_news,
    get_latest_news,
    get_news_by_category,
    get_news_by_source,
    get_today_news,
    get_recent_news,
)


class TestMySQLNewsRepository(unittest.TestCase):

    def setUp(self):
        """Verify DB connection before each test."""
        self.assertTrue(test_connection(), "Database connection failed in test setup.")

    def test_01_insert_and_duplicate_prevention(self):
        """Test inserting a single article and skipping duplicate insert."""
        unique_suffix = int(datetime.utcnow().timestamp())
        test_article = {
            "title": f"Test Headline {unique_suffix}",
            "summary": "This is a test news summary for automated testing.",
            "url": f"https://example.com/news/test-{unique_suffix}",
            "source": "UnitTest Source",
            "published_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "author": "Unit Tester",
            "category": "technology",
            "language": "English",
        }

        # First insertion should succeed
        inserted = insert_news(test_article)
        self.assertTrue(inserted, "First insert should return True.")

        # Re-inserting exact same URL should be skipped automatically
        re_inserted = insert_news(test_article)
        self.assertFalse(re_inserted, "Duplicate URL insert should return False.")

    def test_02_query_functions(self):
        """Test retrieving articles via query functions."""
        latest = get_latest_news(limit=5)
        self.assertIsInstance(latest, list)
        self.assertGreater(len(latest), 0)

        tech_news = get_news_by_category("technology", limit=5)
        self.assertIsInstance(tech_news, list)

        today_news = get_today_news(limit=5)
        self.assertIsInstance(today_news, list)

    def test_03_missing_optional_fields(self):
        """Test inserting an article with missing author, summary, and publication date."""
        unique_suffix = int(datetime.utcnow().timestamp()) + 1
        sparse_article = {
            "title": f"Minimal Article {unique_suffix}",
            "url": f"https://example.com/minimal-{unique_suffix}",
            "source": "Minimal Source",
            # author, summary, published_at intentionally omitted
        }

        inserted = insert_news(sparse_article)
        self.assertTrue(inserted, "Sparse article insertion should succeed without error.")


if __name__ == "__main__":
    unittest.main()

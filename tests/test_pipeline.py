"""
Unit Test Suite for Global News AI - Phase 1

Tests RSS parsing, missing fields handling, HTML cleaning, date normalization,
duplicate detection, and invalid feed URL handling using Python's unittest module.
"""

import unittest
from src.cleaner import (
    clean_html,
    clean_whitespace,
    normalize_date,
    normalize_url,
    clean_article,
    deduplicate_articles,
)
from src.rss_collector import extract_article_fields, fetch_feed_articles


class TestRSSPipeline(unittest.TestCase):

    def test_html_cleaning(self):
        """Test 1: Verifies raw HTML tags and whitespace are stripped cleanly."""
        raw_html = "<p>Breaking: <b>Tech</b> innovation announced <a href='#'>here</a>!</p>"
        cleaned = clean_whitespace(clean_html(raw_html))
        self.assertEqual(cleaned, "Breaking: Tech innovation announced here !")

    def test_date_parsing(self):
        """Test 2: Verifies heterogeneous date strings are normalized to ISO format."""
        raw_date = "Sat, 22 Aug 2026 18:20:36 GMT"
        normalized = normalize_date(raw_date)
        self.assertEqual(normalized, "2026-08-22 18:20:36")

        # Test invalid date handling fallback
        invalid_date = normalize_date("Not A Valid Date")
        self.assertEqual(invalid_date, "")

    def test_missing_fields_handling(self):
        """Test 3: Verifies missing article fields (e.g. author, summary) get safe defaults."""
        raw_article = {
            "title": "Headline Only Article",
            "url": "http://example.com/news1",
            "published_at": "",
            "author": "",
        }
        cleaned = clean_article(raw_article)
        self.assertIsNotNone(cleaned)
        self.assertEqual(cleaned["author"], "Unknown")
        self.assertEqual(cleaned["summary"], "")

    def test_duplicate_detection(self):
        """Test 4: Verifies duplicate URLs and titles are accurately identified and dropped."""
        articles = [
            {
                "title": "Unique News Headline",
                "url": "http://example.com/article1",
            },
            {
                "title": "Unique News Headline",  # Duplicate Title
                "url": "http://example.com/article2",
            },
            {
                "title": "Another Headline",
                "url": "http://example.com/article1",  # Duplicate URL
            },
            {
                "title": "Different News Story",
                "url": "http://example.com/article3",
            },
        ]
        deduped = deduplicate_articles(articles)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["url"], "http://example.com/article1")
        self.assertEqual(deduped[1]["url"], "http://example.com/article3")

    def test_invalid_feed_handling(self):
        """Test 5: Verifies invalid/broken RSS feed URLs return empty list without crashing."""
        broken_url = "http://invalid-nonexistent-domain-987654.org/rss.xml"
        articles = fetch_feed_articles(broken_url, "Test Source", "test")
        self.setIsInstance = isinstance(articles, list)
        self.assertEqual(len(articles), 0)

    def test_rss_parsing_structure(self):
        """Test 6: Verifies extracted dictionary schema has all required keys."""
        mock_entry = {
            "title": "Mock Title",
            "summary": "Mock Summary",
            "link": "http://example.com/mock",
            "published": "Sat, 22 Aug 2026 12:00:00 GMT",
        }
        extracted = extract_article_fields(mock_entry, "Mock Source", "world")
        expected_keys = {
            "title",
            "summary",
            "url",
            "source",
            "published_at",
            "author",
            "category",
            "language",
        }
        self.assertTrue(expected_keys.issubset(extracted.keys()))
        self.assertEqual(extracted["title"], "Mock Title")
        self.assertEqual(extracted["url"], "http://example.com/mock")


if __name__ == "__main__":
    unittest.main()

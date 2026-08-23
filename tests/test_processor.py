"""
Unit Tests for News Processor & Enrichment Module (Phase 3)
"""

import unittest
import json
from src.news_processor import (
    clean_text,
    validate_article,
    detect_language,
    normalize_category,
    detect_country,
    extract_keywords,
    calculate_quality,
    process_article,
)


class TestNewsProcessor(unittest.TestCase):

    def test_01_text_cleaning(self):
        """Test HTML entity decoding, HTML tag stripping, and NFKC normalization."""
        raw = "<p>India&nbsp;announces&nbsp;new&nbsp;AI&nbsp;policy &amp; tech framework!</p>"
        cleaned = clean_text(raw)
        self.assertEqual(cleaned, "India announces new AI policy & tech framework!")

    def test_02_validation(self):
        """Test article validation logic."""
        valid_article = {
            "title": "Valid Headline",
            "url": "https://example.com/valid",
            "source": "BBC News",
        }
        is_valid, _ = validate_article(valid_article)
        self.assertTrue(is_valid)

        invalid_article = {"title": "No URL Article", "source": "BBC News"}
        is_valid_inv, reason = validate_article(invalid_article)
        self.assertFalse(is_valid_inv)
        self.assertIn("url", reason)

    def test_03_language_detection(self):
        """Test language detection and short text fallback."""
        en_text = "The president hosted foreign ministers in Paris today for high-level diplomatic talks."
        self.assertEqual(detect_language(en_text), "English")

        short_text = "Short text"
        self.assertEqual(detect_language(short_text, fallback_lang="English"), "English")

    def test_04_category_normalization(self):
        """Test mapping raw source categories to standard category taxonomy."""
        self.assertEqual(normalize_category("Tech News"), "Technology")
        self.assertEqual(normalize_category("science & technology"), "Technology")
        self.assertEqual(normalize_category("Business & Economy"), "Business")
        self.assertEqual(normalize_category("world"), "World")
        self.assertEqual(normalize_category("football"), "Sports")

    def test_05_country_detection(self):
        """Test country keyword pattern detection."""
        self.assertEqual(detect_country("India announces new technology policy"), "India")
        self.assertEqual(detect_country("Macron hosts Saudi Crown Prince in Paris"), "France")
        self.assertEqual(detect_country("US and Canada trade tariffs impact economy"), "United States")
        self.assertEqual(detect_country("Global market overview"), "Global")

    def test_06_keyword_extraction(self):
        """Test lightweight keyword extraction filtering stopwords."""
        title = "India announces new AI policy for technology companies"
        summary = "New Delhi government launches framework."
        keywords = extract_keywords(title, summary, top_n=4)
        self.assertIsInstance(keywords, list)
        self.assertIn("India", keywords)
        self.assertNotIn("for", keywords)

    def test_07_quality_calculation(self):
        """Test quality rating assignment."""
        good_art = {
            "title": "Full Detailed Article Headline Here",
            "url": "https://example.com/good",
            "source": "BBC News",
            "summary": "This is a detailed summary paragraph providing full context.",
        }
        self.assertEqual(calculate_quality(good_art), "valid")

        short_art = {
            "title": "Short",
            "url": "https://example.com/short",
            "source": "BBC News",
            "summary": "",
        }
        self.assertEqual(calculate_quality(short_art), "needs_review")

    def test_08_full_process_article(self):
        """Test master process_article function."""
        raw_art = {
            "title": "French President Macron to host Saudi Crown Prince MBS in Paris",
            "summary": "<p>Energy &amp; bilateral cooperation to dominate discussions.</p>",
            "url": "https://www.aljazeera.com/news/macron-mbs",
            "source": "Al Jazeera",
            "category": "world news",
            "published_at": "2026-08-23 16:12:55",
        }
        processed, msg = process_article(raw_art)
        self.assertIsNotNone(processed)
        self.assertEqual(processed["category"], "World")
        self.assertEqual(processed["country"], "France")
        self.assertEqual(processed["quality_status"], "valid")
        keywords = json.loads(processed["keywords"])
        self.assertIsInstance(keywords, list)


if __name__ == "__main__":
    unittest.main()

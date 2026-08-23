"""
Unit Tests for Phase 5 (RAG + LLM Pipeline)
"""

import unittest
from src.context_builder import build_rag_context, build_user_prompt
from src.rag_pipeline import format_sources_list, answer_news_question, REFUSAL_MESSAGE


class TestRAGPipeline(unittest.TestCase):

    def test_01_context_builder(self):
        """Test formatting retrieved article dicts into clean RAG context blocks."""
        sample_articles = [
            {
                "rank": 1,
                "title": "US & Canada Tariffs Impact",
                "source": "Al Jazeera",
                "published_at": "2026-08-23",
                "country": "Canada",
                "summary": "Both countries will suffer from trade war.",
            }
        ]
        context = build_rag_context(sample_articles)
        self.assertIn("ARTICLE [1]", context)
        self.assertIn("US & Canada Tariffs Impact", context)
        self.assertIn("Al Jazeera", context)

        prompt = build_user_prompt("What about tariffs?", context)
        self.assertIn("NEWS CONTEXT:", prompt)
        self.assertIn("USER QUESTION: What about tariffs?", prompt)

    def test_02_source_mapping(self):
        """Test mapping retrieved MySQL records to verified source citations."""
        sample_articles = [
            {
                "rank": 1,
                "title": "Test Headline",
                "source": "BBC News",
                "url": "https://bbc.com/news/123",
                "published_at": "2026-08-23 10:00:00",
                "country": "United Kingdom",
            }
        ]
        sources = format_sources_list(sample_articles)
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["citation"], "[1]")
        self.assertEqual(sources[0]["url"], "https://bbc.com/news/123")

    def test_03_refusal_on_unsupported_query(self):
        """Test refusal response when query has 0 relevant matches in vector store."""
        # Query about completely unsupported topic with very high min_score threshold
        unsupported_query = "What happened in Antarctica underwater alien base today?"
        res = answer_news_question(unsupported_query, min_score=0.95)
        
        self.assertEqual(res["status"], "insufficient_context")
        self.assertIn(REFUSAL_MESSAGE, res["answer"])
        self.assertEqual(len(res["sources"]), 0)


if __name__ == "__main__":
    unittest.main()

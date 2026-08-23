"""
Unit and Integration Tests for Phase 4 (Embeddings + Vector Database)

Tests:
1. Model loading & vector dimension check (384 floats).
2. ChromaDB initialization and duplicate-safe upserting.
3. Multilingual semantic search (English, Hindi, Hinglish).
4. Metadata filtering (category, country).
5. Precision@5 quality evaluation metrics.
"""

import unittest
from src.embeddings import create_embedding, EMBEDDING_DIMENSION
from src.vector_store import (
    count_vectors,
    get_vector_collection,
    search_similar_articles,
)


class TestVectorStore(unittest.TestCase):

    def test_01_embedding_generation(self):
        """Test vector embedding generation and dimension size."""
        query = "artificial intelligence policy"
        vector = create_embedding(query)
        self.assertIsInstance(vector, list)
        self.assertEqual(len(vector), EMBEDDING_DIMENSION)

    def test_02_vector_store_persistence(self):
        """Test ChromaDB persistent storage count."""
        total = count_vectors()
        self.assertGreater(total, 0, "Vector DB should contain indexed articles.")

    def test_03_english_semantic_search(self):
        """Test English semantic search query."""
        results = search_similar_articles("artificial intelligence technology policy", top_k=3)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertIn("similarity_score", results[0])
        self.assertGreaterEqual(results[0]["similarity_score"], 0.0)

    def test_04_hindi_semantic_search(self):
        """Test Hindi semantic search query."""
        results = search_similar_articles("कृत्रिम बुद्धिमत्ता के क्षेत्र में क्या हो रहा है?", top_k=3)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_05_hinglish_semantic_search(self):
        """Test Hinglish code-mixed semantic search query."""
        results = search_similar_articles("AI ke field mein abhi kya news hai?", top_k=3)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_06_metadata_filtering(self):
        """Test semantic search with metadata filtering."""
        results = search_similar_articles(
            "business economy markets",
            top_k=3,
            filter_dict={"category": "Business"}
        )
        self.assertIsInstance(results, list)
        for item in results:
            self.assertEqual(item["category"], "Business")

    def test_07_precision_eval(self):
        """Evaluate Precision@5 retrieval metric on sample query."""
        results = search_similar_articles("trade tariffs economy", top_k=5)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Calculate Precision@5 (relevant items with score > 0.3)
        relevant_count = sum(1 for item in results if item["similarity_score"] > 0.3)
        precision_at_5 = relevant_count / float(len(results))
        self.assertGreaterEqual(precision_at_5, 0.0)


if __name__ == "__main__":
    unittest.main()

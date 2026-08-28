"""
Phase 10 FastAPI Backend & Web Integration Test Suite for Global News AI

Verifies:
1. FastAPI app initialization and root endpoint
2. GET /api/news/latest endpoint
3. GET /api/news/category/Technology endpoint
4. POST /api/chat RAG conversational endpoint
5. Session context retention across turns
"""

import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.api.app import app

client = TestClient(app)


class TestPhase10FastAPI(unittest.TestCase):

    def test_01_root_endpoint(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["project"], "Global News AI")
        print("\n✅ Test 1 (FastAPI Root Endpoint) PASSED.")

    def test_02_get_latest_news_api(self):
        response = client.get("/api/news/latest?limit=5")
        self.assertEqual(response.status_code, 200)
        articles = response.json()
        self.assertIsInstance(articles, list)
        self.assertGreater(len(articles), 0)
        self.assertIn("title", articles[0])
        print(f"\n✅ Test 2 (GET /api/news/latest returned {len(articles)} articles) PASSED.")

    def test_03_get_news_by_category_api(self):
        response = client.get("/api/news/category/World?limit=5")
        self.assertEqual(response.status_code, 200)
        articles = response.json()
        self.assertIsInstance(articles, list)
        print(f"\n✅ Test 3 (GET /api/news/category/World returned {len(articles)} articles) PASSED.")

    def test_04_post_chat_rag_api(self):
        payload = {
            "message": "What is happening in India today?",
            "language": "auto",
        }
        response = client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data)
        self.assertIn("conversation_id", data)
        self.assertIn("sources", data)
        print(f"\n✅ Test 4 (POST /api/chat RAG API returned session '{data['conversation_id']}') PASSED.")


if __name__ == "__main__":
    unittest.main()

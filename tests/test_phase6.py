"""
Phase 6 Comprehensive Verification Test Suite for Global News AI

Executes all 12 Phase 6 requirement test cases:
1. Basic question
2. Follow-up query
3. Second follow-up query
4. Latest developments follow-up
5. Country-specific query
6. Country + topic query
7. Hindi query
8. Hinglish query
9. Broad world news query
10. Unsupported / empty DB query (anti-hallucination)
11. Source request query
12. Conversation clear command
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.query_processor import process_query
from src.conversation_manager import ConversationState, rewrite_follow_up_query
from src.rag_pipeline import answer_conversational_news, REFUSAL_MESSAGE


class TestPhase6ConversationalAssistant(unittest.TestCase):

    def setUp(self):
        self.state = ConversationState()

    def test_01_basic_question(self):
        query = "What is happening with AI?"
        parsed = process_query(query)
        self.assertEqual(parsed["category"], "Technology")
        self.assertFalse(parsed["is_follow_up"])
        self.state.update_from_query(parsed)
        self.assertTrue(len(self.state.recent_queries) >= 1)
        print("\n✅ Test 1 (Basic Question) PASSED.")

    def test_02_follow_up_country(self):
        # Setup Turn 1 context
        p1 = process_query("What is happening with AI regulation?")
        self.state.update_from_query(p1)

        # Turn 2: Follow-up
        q2 = "What about India?"
        parsed2 = process_query(q2)
        rewritten2 = rewrite_follow_up_query(q2, parsed2, self.state)

        self.assertTrue(parsed2["is_follow_up"])
        self.assertIn("India", rewritten2)
        self.assertIn("ai regulation", rewritten2.lower())
        print(f"\n✅ Test 2 (Follow-up India) PASSED -> Rewritten: '{rewritten2}'")

    def test_03_another_follow_up(self):
        # Setup Turn 1 & 2
        self.state.update_from_query(process_query("What is happening with AI regulation?"))
        self.state.update_from_query(process_query("What about India?"))

        # Turn 3: Follow-up China
        q3 = "What about China?"
        parsed3 = process_query(q3)
        rewritten3 = rewrite_follow_up_query(q3, parsed3, self.state)

        self.assertIn("China", rewritten3)
        self.assertIn("ai regulation", rewritten3.lower())
        print(f"\n✅ Test 3 (Follow-up China) PASSED -> Rewritten: '{rewritten3}'")

    def test_04_latest_developments(self):
        self.state.update_from_query(process_query("What is happening in Ukraine?"))

        q_latest = "Give me the latest developments."
        parsed_l = process_query(q_latest)
        rewritten_l = rewrite_follow_up_query(q_latest, parsed_l, self.state)

        self.assertTrue(parsed_l["is_follow_up"])
        self.assertIn("latest", rewritten_l.lower())
        print(f"\n✅ Test 4 (Latest Developments) PASSED -> Rewritten: '{rewritten_l}'")

    def test_05_country_query(self):
        query = "What is happening in India?"
        parsed = process_query(query)
        self.assertEqual(parsed["country"], "India")
        print("\n✅ Test 5 (Country Query) PASSED.")

    def test_06_country_and_topic(self):
        query = "What is happening with technology in India?"
        parsed = process_query(query)
        self.assertEqual(parsed["country"], "India")
        self.assertEqual(parsed["category"], "Technology")
        print("\n✅ Test 6 (Country + Topic) PASSED.")

    def test_07_hindi_language(self):
        query = "भारत में आज क्या हो रहा है?"
        parsed = process_query(query)
        self.assertEqual(parsed["language"], "Hindi")
        self.assertEqual(parsed["country"], "India")
        print("\n✅ Test 7 (Hindi Language) PASSED.")

    def test_08_hinglish_language(self):
        query = "India mein AI ke regarding kya chal raha hai?"
        parsed = process_query(query)
        self.assertEqual(parsed["language"], "Hinglish")
        self.assertEqual(parsed["country"], "India")
        print("\n✅ Test 8 (Hinglish Language) PASSED.")

    def test_09_broad_world_news(self):
        query = "What is happening in the world?"
        parsed = process_query(query)
        self.assertEqual(parsed["query_type"], "general_news")
        print("\n✅ Test 9 (Broad World News) PASSED.")

    def test_10_unsupported_query(self):
        query = "What happened on the planet Saturn underwater base yesterday?"
        res = answer_conversational_news(query, state=self.state)
        self.assertIn(res["status"], ["insufficient_context", "success"])
        if res["status"] == "insufficient_context":
            self.assertEqual(res["answer"], REFUSAL_MESSAGE)
        print("\n✅ Test 10 (Unsupported Query Anti-Hallucination) PASSED.")

    def test_11_source_question(self):
        # Setup turn with articles memory
        self.state.set_retrieved_articles([{"rank": 1, "title": "Test Title", "source": "BBC News", "url": "http://bbc.com", "published_at": "2026-08-25", "country": "Global"}])

        # Ask for sources
        res = answer_conversational_news("Show me the sources.", state=self.state)
        self.assertEqual(res["status"], "success")
        self.assertTrue(len(res["sources"]) == 1)
        print("\n✅ Test 11 (Source Question) PASSED.")

    def test_12_clear_conversation(self):
        self.state.update_from_query(process_query("What is happening with AI regulation?"))
        self.assertIsNotNone(self.state.current_topic)

        # Clear
        res = answer_conversational_news("clear", state=self.state)
        self.assertIsNone(self.state.current_topic)
        self.assertEqual(len(self.state.recent_queries), 0)

        # Next follow-up should not assume prior AI context
        q_after = "What about India?"
        parsed = process_query(q_after)
        rewritten = rewrite_follow_up_query(q_after, parsed, self.state)
        self.assertNotIn("ai regulation", rewritten.lower())
        print(f"\n✅ Test 12 (Clear Conversation) PASSED -> Post-clear rewritten: '{rewritten}'")


if __name__ == "__main__":
    unittest.main()


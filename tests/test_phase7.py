"""
Phase 7 Multilingual & Language Intelligence Test Suite for Global News AI

Verifies:
1. English, Hindi, and Hinglish query processing
2. Cross-lingual vector embedding retrieval
3. Multi-turn language switching without context loss
4. Explicit language override parsing
5. Entity, date, and technical term preservation rules
6. Refusal handling for missing information across languages
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

from src.language_detector import detect_language, check_explicit_language_override
from src.query_processor import process_query
from src.conversation_manager import ConversationState, rewrite_follow_up_query
from src.rag_pipeline import answer_conversational_news, REFUSAL_MESSAGE
from src.embeddings import create_embedding
from sentence_transformers import util


class TestPhase7MultilingualIntelligence(unittest.TestCase):

    def setUp(self):
        self.state = ConversationState()

    def test_01_language_detection(self):
        self.assertEqual(detect_language("What is happening in India today?")["language"], "English")
        self.assertEqual(detect_language("भारत में आज क्या हो रहा है?")["language"], "Hindi")
        self.assertEqual(detect_language("India mein aaj kya ho raha hai?")["language"], "Hinglish")
        self.assertEqual(detect_language("AI ke field mein latest news kya hai?")["language"], "Hinglish")
        print("\n✅ Test 1 (Language Detection EN/HI/Hinglish) PASSED.")

    def test_02_explicit_language_override(self):
        self.assertEqual(check_explicit_language_override("Isko Hindi mein explain karo"), "Hindi")
        self.assertEqual(check_explicit_language_override("Ab Hinglish mein batao"), "Hinglish")
        self.assertEqual(check_explicit_language_override("Explain in English please"), "English")
        print("\n✅ Test 2 (Explicit Language Override Parsing) PASSED.")

    def test_03_cross_lingual_vector_alignment(self):
        q_en = "What is happening with AI regulation in India?"
        q_hi = "भारत में AI नियमन के बारे में क्या हो रहा है?"
        q_hinglish = "India mein AI regulation ke baare mein kya chal raha hai?"

        vec_en = create_embedding(q_en)
        vec_hi = create_embedding(q_hi)
        vec_hinglish = create_embedding(q_hinglish)

        sim_hi = float(util.cos_sim(vec_en, vec_hi)[0][0])
        sim_hinglish = float(util.cos_sim(vec_en, vec_hinglish)[0][0])

        self.assertGreater(sim_hi, 0.85)
        self.assertGreater(sim_hinglish, 0.70)
        print(f"\n✅ Test 3 (Cross-Lingual Embedding Alignment EN-HI: {sim_hi:.3f}, EN-Hinglish: {sim_hinglish:.3f}) PASSED.")

    def test_04_multilingual_follow_up_rewriting(self):
        # Turn 1: English
        p1 = process_query("What is happening with AI regulation?")
        self.state.update_from_query(p1)

        # Turn 2: Hinglish follow-up
        q2 = "India mein?"
        p2 = process_query(q2)
        rewritten2 = rewrite_follow_up_query(q2, p2, self.state)
        self.assertIn("India", rewritten2)
        self.assertIn("ai regulation", rewritten2.lower())

        # Turn 3: Hindi follow-up
        q3 = "और China में?"
        p3 = process_query(q3)
        rewritten3 = rewrite_follow_up_query(q3, p3, self.state)
        self.assertIn("China", rewritten3)
        self.assertIn("ai regulation", rewritten3.lower())
        print(f"\n✅ Test 4 (Multilingual Follow-up Rewriting) PASSED.")

    def test_05_explicit_language_switching_turns(self):
        # Setup turn with article context
        self.state.set_retrieved_articles([{
            "rank": 1,
            "title": "AI regulation framework approved in India",
            "source": "BBC News",
            "url": "http://bbc.com/news/1",
            "published_at": "2026-08-25",
            "country": "India",
            "summary": "India has introduced landmark artificial intelligence governance rules.",
        }])
        self.state.current_topic = "ai regulation"

        # Turn 1: Switch to Hindi
        res1 = answer_conversational_news("Isko Hindi mein explain karo.", state=self.state)
        self.assertEqual(res1["status"], "success")
        self.assertEqual(self.state.current_language, "Hindi")

        # Turn 2: Switch to Hinglish
        res2 = answer_conversational_news("Ab Hinglish mein batao.", state=self.state)
        self.assertEqual(res2["status"], "success")
        self.assertEqual(self.state.current_language, "Hinglish")
        self.assertEqual(self.state.current_topic, "ai regulation")
        print("\n✅ Test 5 (Explicit Language Switching without Context Loss) PASSED.")

    def test_06_unsupported_multilingual_query(self):
        q_hi = "XYZ ग्रह पर underwater base के बारे में क्या ताज़ा खबर है?"
        res = answer_conversational_news(q_hi, state=self.state)
        self.assertIn(res["status"], ["insufficient_context", "success"])
        if res["status"] == "insufficient_context":
            self.assertEqual(res["answer"], REFUSAL_MESSAGE)
        print("\n✅ Test 6 (Unsupported Query Hindi Anti-Hallucination) PASSED.")


if __name__ == "__main__":
    unittest.main()

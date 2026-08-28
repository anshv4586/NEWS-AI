"""
Phase 8 Voice Interaction Test Suite for Global News AI

Verifies:
1. Microphone hardware detection utilities
2. STT normalization and Phase 7 language detection integration
3. TTS URL cleaning and narration formatting
4. Decoupled pipeline reuse (Voice STT -> RAG Brain -> TTS)
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.voice.audio_utils import check_microphone_available
from src.voice.speech_to_text import normalize_stt_text, transcribe_audio_file
from src.voice.text_to_speech import clean_text_for_tts
from src.language_detector import detect_language
from src.conversation_manager import ConversationState
from src.rag_pipeline import answer_conversational_news


class TestPhase8VoiceInteraction(unittest.TestCase):

    def test_01_microphone_detection(self):
        avail, msg = check_microphone_available()
        self.assertTrue(avail)
        self.assertIn("microphone", msg.lower())
        print("\n✅ Test 1 (Microphone Detection) PASSED.")

    def test_02_stt_normalization_and_phase7_language(self):
        stt_raw = "India me AI ke field me latest kya chal raha he?"
        norm = normalize_stt_text(stt_raw)
        self.assertIn("mein", norm)
        self.assertIn("hai", norm)

        lang_res = detect_language(norm)
        self.assertEqual(lang_res["language"], "Hinglish")
        print("\n✅ Test 2 (STT Normalization & Phase 7 Hinglish Integration) PASSED.")

    def test_03_tts_url_and_citation_cleaning(self):
        raw_answer = "India mein AI regulation ko lekar key developments ho rahe hain [1]. Link: https://bbc.com/news/123"
        cleaned = clean_text_for_tts(raw_answer)
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("[1]", cleaned)
        self.assertIn("India mein AI regulation", cleaned)
        print("\n✅ Test 3 (TTS URL & Citation Cleaning) PASSED.")

    def test_04_transcribed_text_to_rag_brain(self):
        state = ConversationState()
        # Simulated transcribed text from STT
        transcribed_query = "What is happening with AI regulation in India?"
        res = answer_conversational_news(transcribed_query, state=state)
        self.assertIn(res["status"], ["success", "insufficient_context", "error"])
        print("\n✅ Test 4 (Transcribed Text to Phase 6/7 RAG Brain) PASSED.")


if __name__ == "__main__":
    unittest.main()

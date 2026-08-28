"""
Conversational Voice Shell Interface for Global News AI - Phase 8

Provides an interactive microphone & speaker voice shell allowing users to:
1. Speak news questions in English, Hindi, or Hinglish.
2. Transcribe speech to text via STT.
3. Query the existing Phase 6 + Phase 7 Conversational RAG Engine.
4. Display grounded text answers with clickable sources.
5. Speak responses via TTS in native language.
"""

import sys
import time
import logging
from typing import Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.conversation_manager import ConversationState
from src.rag_pipeline import answer_conversational_news
from src.voice.audio_utils import (
    check_microphone_available,
    record_microphone_audio,
    cleanup_temp_audio_file,
)
from src.voice.speech_to_text import transcribe_audio_file
from src.voice.text_to_speech import speak_text

logger = logging.getLogger(__name__)


def run_voice_chat_session():
    """
    Main interactive Voice Chat Shell loop.
    """
    print("\n" + "=" * 80)
    print(" 🎤 GLOBAL NEWS AI - CONVERSATIONAL VOICE ASSISTANT (PHASE 8)")
    print("=" * 80)
    
    mic_avail, mic_msg = check_microphone_available()
    if not mic_avail:
        print(f"\n❌ Microphone Error: {mic_msg}")
        print("Please connect a microphone device and try again.")
        return

    print(" [INFO] Microphone Ready! STT: Google Speech | TTS: Google Speech Synthesis")
    print(" [INFO] Languages: English | Hindi (हिंदी) | Hinglish")
    print(" [INFO] Commands: Say 'stop', 'exit', 'quit' to end | Say 'clear' to reset context")
    print("-" * 80 + "\n")

    state = ConversationState()

    while True:
        try:
            t0 = time.time()

            # Step 1: Record Microphone Audio
            wav_path, audio_data = record_microphone_audio(max_duration=30, timeout=8)
            t_record = time.time() - t0

            if not audio_data:
                print("⚠️  No speech detected. Please try speaking again.")
                continue

            # Step 2: Speech-to-Text Transcription
            t1 = time.time()
            stt_res = transcribe_audio_file(audio_data)
            t_stt = time.time() - t1

            if stt_res["status"] != "success" or not stt_res["text"]:
                print("⚠️  Could not understand audio clearly. Please try speaking again.")
                cleanup_temp_audio_file(wav_path)
                continue

            user_text = stt_res["text"]
            detected_lang = stt_res["language"]

            print(f"\n🗣️  You (Spoken) : {user_text}")
            print(f"🌐 Detected Lang : {detected_lang} (STT Code: {stt_res.get('stt_language_code')})")

            # Check for exit commands
            if user_text.lower().strip() in ("exit", "quit", "stop", "bye"):
                print("\n👋 Goodbye! Voice session ended.")
                cleanup_temp_audio_file(wav_path)
                break

            # Step 3: Pass Transcribed Text to Existing Phase 6/7 RAG Pipeline
            t2 = time.time()
            rag_res = answer_conversational_news(user_text, state=state)
            t_rag = time.time() - t2

            # Step 4: Display Formatted Response & Sources on Screen
            print("\n" + rag_res["formatted_response"])

            # Step 5: Speak Answer via Text-to-Speech (TTS)
            answer_text = rag_res["answer"]
            target_lang = state.current_language or detected_lang

            t3 = time.time()
            if rag_res["status"] == "success" and answer_text:
                speak_text(answer_text, language=target_lang, play_audio=True)
            t_tts = time.time() - t3

            # Report Latency Metrics
            total_latency = t_record + t_stt + t_rag + t_tts
            logger.info(
                f"[Voice Latency] Rec: {t_record:.1f}s | STT: {t_stt:.1f}s | RAG: {t_rag:.1f}s | "
                f"TTS: {t_tts:.1f}s | Total: {total_latency:.1f}s"
            )

            # Cleanup temp audio
            cleanup_temp_audio_file(wav_path)
            print("\n" + "-" * 80)

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Exiting Voice Assistant.")
            break
        except Exception as err:
            logger.error(f"[Voice Shell Error]: {err}")
            print(f"\n⚠️  Voice Session Error: {err}")
            time.sleep(1)


if __name__ == "__main__":
    run_voice_chat_session()

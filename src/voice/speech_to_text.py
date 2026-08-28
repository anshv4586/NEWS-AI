"""
Speech-to-Text (STT) Module for Global News AI - Phase 8

Provides high-accuracy transcription of spoken audio into clean text supporting:
- English
- Hindi (Devanagari script)
- Hinglish (Code-switched Romanized Hindi)

Integrates directly with Phase 7 language_detector for seamless downstream processing.
"""

import logging
from typing import Any, Dict, Optional
from src.language_detector import detect_language

logger = logging.getLogger(__name__)


def normalize_stt_text(text: str) -> str:
    """
    Applies lightweight normalization to common STT transcription variations
    (e.g., 'me' -> 'mein', 'he' -> 'hai') without altering entity names or meaning.
    """
    if not text:
        return ""
        
    normalized = text.strip()
    
    # Common STT phonetic replacements for Hinglish
    replacements = [
        (" me ", " mein "),
        (" me?", " mein?"),
        (" he ", " hai "),
        (" he?", " hai?"),
    ]
    for old, new in replacements:
        normalized = normalized.replace(old, new)

    return normalized


def transcribe_audio_file(
    audio_data: Any,
    preferred_language: str = "auto",
) -> Dict[str, Any]:
    """
    Transcribes SpeechRecognition AudioData or WAV file into text using SpeechRecognition.
    Supports English ('en-IN', 'en-US') and Hindi ('hi-IN').
    
    Returns structured dictionary:
    - text: str
    - language: str ('English', 'Hindi', 'Hinglish')
    - stt_provider: 'google'
    - status: 'success' or 'error'
    """
    if not audio_data:
        return {
            "text": "",
            "language": "English",
            "stt_provider": "google",
            "status": "empty_audio",
        }

    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()

        transcription = ""
        used_lang = "en-IN"

        # Determine STT target language code
        if preferred_language == "hi":
            lang_codes = ["hi-IN", "en-IN"]
        elif preferred_language == "en":
            lang_codes = ["en-IN", "en-US"]
        else:
            lang_codes = ["en-IN", "hi-IN", "en-US"]

        # Attempt transcription across preferred language models
        for code in lang_codes:
            try:
                raw_text = recognizer.recognize_google(audio_data, language=code)
                if raw_text and len(raw_text.strip()) >= 2:
                    transcription = raw_text.strip()
                    used_lang = code
                    logger.info(f"[STT] Transcribed audio using language code '{code}': '{transcription}'")
                    break
            except Exception:
                continue

        if not transcription:
            logger.warning("[STT] Could not transcribe audio into clear speech text.")
            return {
                "text": "",
                "language": "English",
                "stt_provider": "google",
                "status": "unrecognized_speech",
            }

        # Normalize text
        clean_text = normalize_stt_text(transcription)

        # Detect native/spoken language via Phase 7 Language Detector
        lang_info = detect_language(clean_text)
        detected_lang = lang_info["language"]

        return {
            "text": clean_text,
            "raw_stt_text": transcription,
            "language": detected_lang,
            "stt_language_code": used_lang,
            "stt_provider": "google",
            "confidence": lang_info.get("confidence", 0.90),
            "status": "success",
        }

    except Exception as err:
        logger.error(f"[STT] Speech-to-Text transcription error: {err}")
        return {
            "text": "",
            "language": "English",
            "stt_provider": "google",
            "status": "error",
            "error_details": str(err),
        }


if __name__ == "__main__":
    import sys
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("\n--- SPEECH-TO-TEXT MODULE AUDIT ---\n")
    sample_text = "India me AI ke field me latest kya chal raha he?"
    norm = normalize_stt_text(sample_text)
    detected = detect_language(norm)
    print(f"Sample Input : {sample_text}")
    print(f"Normalized   : {norm}")
    print(f"Phase 7 Lang : {detected['language']} (Conf: {detected['confidence']})\n")

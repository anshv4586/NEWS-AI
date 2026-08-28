"""
Text-to-Speech (TTS) & Audio Playback Module for Global News AI - Phase 8

Provides high-quality speech synthesis for:
- English
- Hindi (Devanagari script)
- Hinglish (Natural Indian English/Hindi accent)

Filters out raw URLs from audio narration (Requirement #20) and enforces immediate privacy cleanup.
"""

import os
import re
import time
import tempfile
import logging
from typing import Optional
from src.voice.audio_utils import cleanup_temp_audio_file

logger = logging.getLogger(__name__)


def clean_text_for_tts(text: str) -> str:
    """
    Cleans text answer before sending to TTS engine:
    - Removes raw URLs (e.g. 'https://bbc.com/news') so speaker doesn't read out 'https colon slash...'
    - Strips markdown formatting symbols (*, #, _, `)
    - Replaces citation brackets like '[1]' with clean pauses
    """
    if not text:
        return ""

    # Remove URLs
    cleaned = re.sub(r"https?://\S+", "", text)
    # Remove markdown headers and formatting
    cleaned = re.sub(r"[#\*_`\-\[\]]", " ", cleaned)
    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def play_audio_file(audio_filepath: str):
    """
    Plays an MP3/WAV audio file safely using pygame.mixer.
    """
    if not audio_filepath or not os.path.exists(audio_filepath):
        logger.warning(f"[TTS Playback] Audio file not found: '{audio_filepath}'")
        return

    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(audio_filepath)
        pygame.mixer.music.play()

        logger.info(f"[TTS Playback] Playing audio response: '{audio_filepath}'...")
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.quit()
        logger.info("[TTS Playback] Audio playback completed.")

    except Exception as err:
        logger.warning(f"[TTS Playback] Pygame playback error: {err}. Falling back to OS default player...")
        try:
            if os.name == "nt":
                os.system(f'start "" /min "{audio_filepath}"')
                time.sleep(3)
        except Exception as os_err:
            logger.error(f"[TTS Playback] OS playback fallback failed: {os_err}")


def speak_text(
    text: str,
    language: str = "English",
    play_audio: bool = True,
    tts_provider: str = "gtts",
) -> Optional[str]:
    """
    Synthesizes speech from text answer matching user's language (English, Hindi, Hinglish).
    
    Parameters:
    - text: str (raw response text)
    - language: str ('English', 'Hindi', 'Hinglish')
    - play_audio: bool (play immediately through speakers)
    - tts_provider: str ('gtts')
    
    Returns:
    - path to temporary MP3 file or None
    """
    cleaned = clean_text_for_tts(text)
    if not cleaned:
        logger.warning("[TTS] Empty text provided for TTS synthesis.")
        return None

    # Map Phase 7 language to gTTS language code
    if language == "Hindi":
        lang_code = "hi"
    elif language == "Hinglish":
        lang_code = "hi"  # Natural Devanagari/Hindi voice engine for Hinglish terms
    else:
        lang_code = "en"

    temp_dir = tempfile.gettempdir()
    temp_mp3 = os.path.join(temp_dir, f"tts_response_{os.getpid()}_{int(time.time())}.mp3")

    try:
        from gtts import gTTS
        logger.info(f"[TTS] Synthesizing speech (Lang Code: '{lang_code}', Text length: {len(cleaned)} chars)...")
        tts = gTTS(text=cleaned, lang=lang_code, slow=False)
        tts.save(temp_mp3)

        if play_audio and os.path.exists(temp_mp3):
            print("\n🔊 [Speaking answer...]")
            play_audio_file(temp_mp3)

        return temp_mp3

    except Exception as err:
        logger.error(f"[TTS] Text-to-Speech synthesis failed: {err}")
        print("\n⚠️  [WARNING: Voice playback unavailable. Text response displayed above.]")
        return None
    finally:
        # Enforce Privacy Requirement #28
        cleanup_temp_audio_file(temp_mp3)


if __name__ == "__main__":
    import sys
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("\n--- TEXT-TO-SPEECH MODULE AUDIT ---\n")
    sample_text = "India mein AI regulation ko lekar key developments ho rahe hain [1]. Link: https://bbc.com/news/123"
    cleaned = clean_text_for_tts(sample_text)
    print(f"Original Text : {sample_text}")
    print(f"Cleaned TTS   : {cleaned}")

"""
Audio Utilities & Safe Microphone Recording Module for Global News AI - Phase 8

Handles safe microphone detection, duration-capped recording, temporary WAV file generation,
and immediate privacy cleanup of temporary audio files.
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)


def check_microphone_available() -> Tuple[bool, str]:
    """
    Checks if PyAudio / SpeechRecognition detects an active microphone device.
    """
    try:
        import speech_recognition as sr
        mics = sr.Microphone.list_microphone_names()
        if not mics:
            return False, "No microphone input device detected on this system."
        logger.info(f"[Audio Utils] Detected {len(mics)} microphone input devices.")
        return True, f"Found {len(mics)} microphone(s)."
    except Exception as err:
        logger.warning(f"[Audio Utils] Microphone check failed: {err}")
        return False, str(err)


def record_microphone_audio(
    max_duration: int = 30,
    timeout: int = 5,
) -> Tuple[Optional[str], Optional[Any]]:
    """
    Records speech from default microphone up to max_duration seconds using SpeechRecognition.
    Returns temporary WAV file path and SpeechRecognition AudioData object.
    Automatically handles silence timeouts, empty recordings, and errors safely.
    """
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        # Adjust energy threshold for ambient noise
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 1.2

        is_avail, msg = check_microphone_available()
        if not is_avail:
            logger.error(f"[Audio Utils] Cannot record: {msg}")
            return None, None

        logger.info(f"[Audio Utils] Listening on microphone (Timeout: {timeout}s, Max duration: {max_duration}s)...")
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            print("\n🎤 [Listening...] Speak your news question now (Press Ctrl+C to stop)...")
            audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=max_duration)
            print("⏹️  [Recording stopped. Processing audio...]")

        # Create temporary WAV file for STT processing
        temp_dir = tempfile.gettempdir()
        temp_wav = os.path.join(temp_dir, f"news_voice_{os.getpid()}.wav")
        with open(temp_wav, "wb") as f:
            f.write(audio_data.get_wav_data())

        logger.info(f"[Audio Utils] Audio recorded successfully to temp file: '{temp_wav}'")
        return temp_wav, audio_data

    except Exception as err:
        err_name = type(err).__name__
        if "WaitTimeoutError" in err_name or "WaitTimeout" in str(err):
            logger.warning("[Audio Utils] Listening timed out. No speech was detected.")
        else:
            logger.error(f"[Audio Utils] Error during microphone recording: {err}")
        return None, None


def cleanup_temp_audio_file(filepath: Optional[str]):
    """
    Enforces privacy requirement #28 by deleting temporary audio files immediately after use.
    """
    if not filepath or not os.path.exists(filepath):
        return

    try:
        os.remove(filepath)
        logger.info(f"[Privacy Cleanup] Deleted temporary audio file: '{filepath}'")
    except Exception as err:
        logger.warning(f"[Privacy Cleanup] Failed to delete temporary audio file '{filepath}': {err}")


if __name__ == "__main__":
    import sys
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("\n--- MICROPHONE AUDIT & AUDIO UTILS TEST ---\n")
    avail, status_msg = check_microphone_available()
    print(f"Microphone Available: {avail}")
    print(f"Status Message      : {status_msg}\n")

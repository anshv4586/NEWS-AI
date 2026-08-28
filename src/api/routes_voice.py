"""
Voice Interaction REST API Routes for Global News AI - Phase 10

Provides endpoints for:
- POST /api/voice/chat (Accepts audio file upload -> STT -> RAG -> TTS -> Returns response & audio)
"""

import os
import base64
import tempfile
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from src.api.routes_chat import get_or_create_session
from src.rag_pipeline import answer_conversational_news
from src.voice.speech_to_text import transcribe_audio_file
from src.voice.text_to_speech import speak_text, clean_text_for_tts
from src.voice.audio_utils import cleanup_temp_audio_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["Voice Input & Output Integration"])


@router.post("/chat")
async def post_voice_chat(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    language: Optional[str] = Form("auto"),
):
    """
    Processes voice speech audio recording:
    1. Transcribes audio to text via STT.
    2. Executes Phase 6/7 RAG Pipeline.
    3. Synthesizes text answer to speech via TTS.
    4. Returns JSON response with base64 encoded MP3 audio stream for browser playback.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No audio file uploaded.")

    # Save uploaded file temporarily
    temp_dir = tempfile.gettempdir()
    temp_filename = f"voice_upload_{os.getpid()}_{file.filename}"
    temp_filepath = os.path.join(temp_dir, temp_filename)

    try:
        content = await file.read()
        with open(temp_filepath, "wb") as f:
            f.write(content)

        # Transcribe audio file to text using SpeechRecognition
        import speech_recognition as sr
        recognizer = sr.Recognizer()

        transcribed_text = ""
        try:
            with sr.AudioFile(temp_filepath) as source:
                audio_data = recognizer.record(source)
                stt_res = transcribe_audio_file(audio_data)
                transcribed_text = stt_res.get("text", "")
        except Exception as stt_err:
            logger.warning(f"AudioFile transcription error: {stt_err}")

        if not transcribed_text:
            cleanup_temp_audio_file(temp_filepath)
            return {
                "status": "unrecognized_speech",
                "user_message": "",
                "answer": "I could not understand the speech clearly. Please try speaking again.",
                "sources": [],
                "audio_base64": None,
            }

        # Process query through RAG pipeline
        cid, state = get_or_create_session(conversation_id)
        rag_res = answer_conversational_news(transcribed_text, state=state)
        answer_text = rag_res.get("answer", "")

        # Synthesize TTS Audio
        audio_b64 = None
        target_lang = state.current_language or "English"
        
        mp3_path = speak_text(answer_text, language=target_lang, play_audio=False)
        if mp3_path and os.path.exists(mp3_path):
            with open(mp3_path, "rb") as audio_f:
                audio_b64 = base64.b64encode(audio_f.read()).decode("utf-8")
            cleanup_temp_audio_file(mp3_path)

        cleanup_temp_audio_file(temp_filepath)

        return {
            "status": "success",
            "conversation_id": cid,
            "user_message": transcribed_text,
            "answer": answer_text,
            "language": target_lang,
            "sources": rag_res.get("sources", []),
            "audio_base64": audio_b64,
        }

    except Exception as err:
        cleanup_temp_audio_file(temp_filepath)
        logger.error(f"Voice Chat API Error: {err}")
        raise HTTPException(status_code=500, detail=f"Voice processing error: {err}")

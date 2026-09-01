"""
Chat & Conversation Session API Routes for Global News AI - Phase 10

Provides endpoints for:
- POST /api/chat (Conversational news query with RAG & multilingual grounding)
- POST /api/chat/clear (Reset conversation state memory)
"""

import uuid
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.conversation_manager import ConversationState
from src.rag_pipeline import answer_conversational_news


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Conversational RAG Chat"])

# Global session store mapping conversation_id -> ConversationState
SESSION_STORE: Dict[str, ConversationState] = {}


def get_or_create_session(conversation_id: Optional[str] = None) -> Tuple[str, ConversationState]:
    """
    Retrieves or initializes a ConversationState instance for the given conversation_id.
    """
    if not conversation_id or conversation_id.strip() == "":
        new_id = f"conv_{uuid.uuid4().hex[:12]}"
        SESSION_STORE[new_id] = ConversationState()
        return new_id, SESSION_STORE[new_id]

    cid = conversation_id.strip()
    if cid not in SESSION_STORE:
        SESSION_STORE[cid] = ConversationState()

    return cid, SESSION_STORE[cid]


class Tuple_Session:
    pass


class ChatRequest(BaseModel):
    message: str = Field(..., description="User query message", example="What is happening in India today?")
    conversation_id: Optional[str] = Field(None, description="Optional conversation session ID for context retention", example="conv_abc123")
    language: Optional[str] = Field("auto", description="Target language ('auto', 'English', 'Hindi', 'Hinglish')", example="auto")


def format_published_at_str(val: Any) -> Optional[str]:
    """
    Safely converts datetime objects or arbitrary timestamp representations to a clean string.
    """
    if val is None:
        return None
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    s = str(val).strip()
    return s if s else None


class SourceItem(BaseModel):
    title: str
    source: str
    url: str
    published_at: Optional[Any] = None
    category: Optional[str] = None
    country: Optional[str] = None
    snippet: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    user_message: str
    answer: str
    status: str
    language: str
    sources: List[SourceItem]
    turn_count: int


@router.post("", response_model=ChatResponse)
def post_chat(payload: ChatRequest):
    """
    Executes a conversational RAG news query.
    Reuses existing Phase 6 & Phase 7 RAG pipeline, LLM engine, and language detector.
    """
    query = (payload.message or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="User message cannot be empty.")

    # Retrieve or initialize session state
    cid, state = get_or_create_session(payload.conversation_id)

    # Handle explicit language override if requested
    if payload.language and payload.language.lower() != "auto":
        override_map = {
            "english": "English",
            "hindi": "Hindi",
            "hinglish": "Hinglish",
        }
        target_lang = override_map.get(payload.language.lower(), payload.language)
        if hasattr(state, "set_language"):
            state.set_language(target_lang)
        else:
            state.current_language = target_lang

    try:
        # Call Phase 6/7 Conversational RAG Brain
        rag_res = answer_conversational_news(query, state=state)

        # Structure source cards safely
        structured_sources = []
        for src in rag_res.get("sources", []):
            structured_sources.append(SourceItem(
                title=str(src.get("title") or "News Article"),
                source=str(src.get("source") or "News Publisher"),
                url=str(src.get("url") or "#"),
                published_at=format_published_at_str(src.get("published_at")),
                category=str(src.get("category")) if src.get("category") else None,
                country=str(src.get("country")) if src.get("country") else None,
                snippet=str(src.get("snippet")) if src.get("snippet") else None,
            ))

        return ChatResponse(
            conversation_id=cid,
            user_message=query,
            answer=rag_res.get("answer", "No answer generated."),
            status=rag_res.get("status", "success"),
            language=state.current_language or rag_res.get("detected_language", "English"),
            sources=structured_sources,
            turn_count=len(state.turns),
        )

    except Exception as err:
        logger.error(f"API Chat Error: {err}")
        return ChatResponse(
            conversation_id=cid,
            user_message=query,
            answer=f"I'm currently unable to retrieve the latest news for that query ({str(err)}). Please ensure your LLM API key is configured in your hosting environment settings, or try again in a moment.",
            status="error",
            language=state.current_language or "English",
            sources=[],
            turn_count=len(state.turns),
        )


@router.get("/sessions")

def get_chat_sessions():
    """
    Retrieves summary list of all active conversation sessions.
    """
    sessions_list = []
    for cid, state in SESSION_STORE.items():
        if state.turns:
            first_turn = state.turns[0]
            first_user_query = first_turn.user_query if hasattr(first_turn, "user_query") else first_turn.get("user_query", "Chat Session")
            title = first_user_query[:35] + ("..." if len(first_user_query) > 35 else "")
        else:
            title = "New Chat Session"
            
        sessions_list.append({
            "id": cid,
            "title": title,
            "turn_count": len(state.turns),
            "language": state.current_language or "Auto",
        })
    return {"status": "success", "sessions": sessions_list}


@router.delete("/session/{conversation_id}")
def delete_chat_session(conversation_id: str):
    """
    Deletes a specific chat session from memory.
    """
    cid = conversation_id.strip()
    if cid in SESSION_STORE:
        del SESSION_STORE[cid]
        return {"status": "success", "message": f"Session '{cid}' deleted successfully."}
    return {"status": "not_found", "message": f"Session '{cid}' was not active."}


@router.post("/clear")
def clear_chat_session(conversation_id: str):
    """
    Clears the conversation memory state for a given session.
    """
    cid = conversation_id.strip()
    if cid in SESSION_STORE:
        SESSION_STORE[cid].clear()
        return {"status": "success", "message": f"Session '{cid}' context cleared."}
    return {"status": "not_found", "message": f"Session '{cid}' was not active."}


@router.post("/stream")
async def post_chat_stream(payload: ChatRequest):
    """
    Executes RAG news query and streams response tokens via Server-Sent Events (SSE).
    """
    query = (payload.message or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="User message cannot be empty.")

    cid, state = get_or_create_session(payload.conversation_id)

    if payload.language and payload.language.lower() != "auto":
        override_map = {
            "english": "English",
            "hindi": "Hindi",
            "hinglish": "Hinglish",
        }
        target_lang = override_map.get(payload.language.lower(), payload.language)
        if hasattr(state, "set_language"):
            state.set_language(target_lang)
        else:
            state.current_language = target_lang

    async def event_generator():
        try:
            # Run RAG in executor to avoid blocking asyncio event loop
            loop = asyncio.get_running_loop()
            rag_res = await loop.run_in_executor(None, lambda: answer_conversational_news(query, state=state))

            structured_sources = []
            for src in rag_res.get("sources", []):
                structured_sources.append({
                    "title": str(src.get("title") or "News Article"),
                    "source": str(src.get("source") or "News Publisher"),
                    "url": str(src.get("url") or "#"),
                    "published_at": format_published_at_str(src.get("published_at")),
                    "category": str(src.get("category")) if src.get("category") else None,
                    "country": str(src.get("country")) if src.get("country") else None,
                    "snippet": str(src.get("snippet")) if src.get("snippet") else None,
                })

            # Send metadata payload first
            meta_payload = {
                "type": "meta",
                "conversation_id": cid,
                "language": state.current_language or rag_res.get("detected_language", "English"),
                "sources": structured_sources,
                "status": rag_res.get("status", "success"),
            }
            yield f"data: {json.dumps(meta_payload, default=str)}\n\n"
            await asyncio.sleep(0.02)

            full_answer = rag_res.get("answer", "")
            words = full_answer.split(" ")
            
            # Stream response progressively in 2-3 word chunks
            chunk_size = 2
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size]) + (" " if i + chunk_size < len(words) else "")
                chunk_payload = {
                    "type": "token",
                    "content": chunk,
                }
                yield f"data: {json.dumps(chunk_payload)}\n\n"
                await asyncio.sleep(0.03)

            done_payload = {"type": "done"}
            yield f"data: {json.dumps(done_payload)}\n\n"

        except Exception as err:
            logger.error(f"Streaming Error: {err}")
            err_payload = {"type": "error", "message": str(err)}
            yield f"data: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


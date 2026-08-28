"""
Main FastAPI Server Entry Point for Global News AI - Phase 10

Registers CORS middleware, includes API route modules (Chat, News Data, Voice),
and provides OpenAPI documentation (/docs).

Run backend server with:
    uvicorn src.api.app:app --reload --port 8000
"""

import sys
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure project root in sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.api.routes_chat import router as chat_router
from src.api.routes_news import router as news_router
from src.api.routes_voice import router as voice_router
from src.api.routes_auth import router as auth_router, saved_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Global News AI — Conversational REST API",
    description="Multilingual RAG Grounded News Engine API supporting English, Hindi, Hinglish, Voice & OTP Auth.",
    version="1.0.0",
)

# Configure CORS Middleware for Frontend React App (http://localhost:5173 / http://localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(chat_router)
app.include_router(news_router)
app.include_router(voice_router)
app.include_router(auth_router)
app.include_router(saved_router)



@app.get("/")
def read_root():
    return {
        "project": "Global News AI",
        "phase": "Phase 10 — ChatGPT-like Web Application & FastAPI Backend",
        "status": "online",
        "docs_url": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="127.0.0.1", port=8000, reload=True)

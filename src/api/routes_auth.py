"""
Authentication & Client API Routes for Global News AI

Provides endpoints for client registration, authentication, profile inspection,
and client management into the 'client_db' table.
"""

from typing import Any, Dict, Optional
import logging
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel, EmailStr, Field
from src.auth_repository import (
    register_client,
    authenticate_client,
    get_client_by_id,
    get_client_by_email,
    get_all_clients,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication & Client DB"])


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full Name of the client")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Account password (min 6 characters)")
    country: Optional[str] = Field("Global", description="Country of preference")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Client user preferences")


class LoginRequest(BaseModel):
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def post_register(req: RegisterRequest):
    """
    Registers a new client and persists their record into 'client_db'.
    """
    success, message, client_profile = register_client(
        name=req.name,
        email=req.email,
        password=req.password,
        country=req.country or "Global",
        preferences=req.preferences,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return {
        "status": "success",
        "message": message,
        "client": client_profile,
        "token": f"token_{client_profile.get('id')}_{hash(client_profile.get('email'))}",
    }


@router.post("/login", status_code=status.HTTP_200_OK)
def post_login(req: LoginRequest):
    """
    Authenticates client credentials against 'client_db' and returns active session.
    """
    success, message, client_profile = authenticate_client(
        email=req.email,
        password=req.password,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

    return {
        "status": "success",
        "message": message,
        "client": client_profile,
        "token": f"token_{client_profile.get('id')}_{hash(client_profile.get('email'))}",
    }


@router.get("/me", status_code=status.HTTP_200_OK)
def get_current_user(email: Optional[str] = None):
    """
    Retrieves current client profile information.
    """
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email query parameter required.")

    client = get_client_by_email(email)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found in client_db.")

    return {
        "status": "success",
        "client": client,
    }


@router.get("/clients", status_code=status.HTTP_200_OK)
def list_clients(limit: int = 50):
    """
    Retrieves registered clients from 'client_db' for administrative oversight.
    """
    clients = get_all_clients(limit=limit)
    return {
        "status": "success",
        "count": len(clients),
        "clients": clients,
    }


# Router for Saved/Bookmarked Articles
saved_router = APIRouter(tags=["Saved Articles"])

_SAVED_ARTICLES_MEMORY = []

@saved_router.get("/api/saved", status_code=status.HTTP_200_OK)
@saved_router.get("/api/news/saved", status_code=status.HTTP_200_OK)
def get_saved_articles():
    return _SAVED_ARTICLES_MEMORY

@saved_router.post("/api/saved", status_code=status.HTTP_201_CREATED)
@saved_router.post("/api/news/saved", status_code=status.HTTP_201_CREATED)
def add_saved_article(article: Dict[str, Any]):
    # Prevent exact URL duplicates
    url = article.get("url")
    if url and not any(a.get("url") == url for a in _SAVED_ARTICLES_MEMORY):
        _SAVED_ARTICLES_MEMORY.append(article)
    return {"status": "success", "message": "Article saved successfully."}

@saved_router.delete("/api/saved", status_code=status.HTTP_200_OK)
@saved_router.delete("/api/news/saved", status_code=status.HTTP_200_OK)
def remove_saved_article(url: Optional[str] = None):
    global _SAVED_ARTICLES_MEMORY
    if url:
        _SAVED_ARTICLES_MEMORY = [a for a in _SAVED_ARTICLES_MEMORY if a.get("url") != url]
    return {"status": "success", "message": "Article removed."}

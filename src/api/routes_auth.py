"""
FastAPI Authentication & User Bookmarks Router

Provides endpoints for:
- POST /api/auth/send-otp
- POST /api/auth/verify-otp
- GET  /api/auth/me
- POST /api/auth/logout
- GET  /api/news/saved (User-bound bookmarks)
- POST /api/news/saved
- DELETE /api/news/saved
"""

import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request, Response, Depends, Cookie

from src.auth import (
    request_otp,
    verify_otp,
    create_session,
    get_user_from_session,
    destroy_session,
)
from src.database import execute_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication & User Session"])
saved_router = APIRouter(prefix="/api/news/saved", tags=["User Saved Bookmarks"])


# Request / Response Schemas
class SendOtpRequest(BaseModel):
    identifier: str = Field(..., example="user@example.com")
    auth_type: str = Field("email", example="email")  # 'email' or 'phone'
    country_code: Optional[str] = Field("+91", example="+91")


class VerifyOtpRequest(BaseModel):
    identifier: str = Field(..., example="user@example.com")
    auth_type: str = Field("email", example="email")
    otp_code: str = Field(..., example="123456")
    country_code: Optional[str] = Field("+91", example="+91")


class UserResponse(BaseModel):
    user_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    auth_type: str
    created_at: Optional[str] = None


class SaveArticleRequest(BaseModel):
    url: str
    title: str
    source: str
    published_at: Optional[str] = None


# Dependency to retrieve active authenticated user from session cookie or Authorization header
def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(None)
) -> Optional[Dict[str, Any]]:
    """
    Extracts session token from HTTP-only cookie or Bearer token and returns authenticated user object.
    """
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1].strip()

    if not token:
        return None

    return get_user_from_session(token)


@router.post("/send-otp")
def api_send_otp(payload: SendOtpRequest):
    """
    Validates identifier, rate-limits requests, generates 6-digit OTP,
    hashes & stores OTP in DB, and delivers via Email/SMS or Dev Logger.
    """
    try:
        success, message = request_otp(
            identifier=payload.identifier,
            auth_type=payload.auth_type,
            country_code=payload.country_code or "+91"
        )
        if not success:
            raise HTTPException(status_code=429, detail=message)
        
        return {
            "status": "success",
            "message": message,
            "expires_in_seconds": 300,
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Error in send-otp: {err}")
        raise HTTPException(status_code=500, detail="Internal server error sending OTP code.")


@router.post("/verify-otp")
def api_verify_otp(payload: VerifyOtpRequest, request: Request, response: Response):
    """
    Verifies entered 6-digit OTP against DB hash.
    Upon success, creates session & sets HTTP-only Cookie.
    """
    try:
        success, message, user = verify_otp(
            identifier=payload.identifier,
            auth_type=payload.auth_type,
            plain_otp=payload.otp_code,
            country_code=payload.country_code or "+91"
        )
        if not success or not user:
            raise HTTPException(status_code=400, detail=message)

        # Create session and set HTTP-only cookie
        user_agent = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None
        session_id, expires_at = create_session(user["user_id"], user_agent, ip_address)

        # Set HTTP-only Cookie
        response.set_cookie(
            key="session_token",
            value=session_id,
            httponly=True,
            samesite="lax",
            secure=False,  # Set to True in HTTPS production environments
            max_age=7 * 86400
        )

        return {
            "status": "success",
            "message": "Authentication successful.",
            "user": {
                "user_id": user["user_id"],
                "email": user.get("email"),
                "phone": user.get("phone"),
                "auth_type": user["auth_type"],
                "created_at": str(user.get("created_at") or ""),
            }
        }
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Error in verify-otp: {err}")
        raise HTTPException(status_code=500, detail="Internal server error verifying OTP code.")


@router.get("/me")
def api_get_current_user(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """
    Returns current authenticated user session data if valid.
    """
    if not current_user:
        return {"authenticated": False, "user": None}

    return {
        "authenticated": True,
        "user": {
            "user_id": current_user["user_id"],
            "email": current_user.get("email"),
            "phone": current_user.get("phone"),
            "auth_type": current_user["auth_type"],
            "created_at": str(current_user.get("created_at") or ""),
        }
    }


@router.post("/logout")
def api_logout(request: Request, response: Response, session_token: Optional[str] = Cookie(None)):
    """
    Destroys active user session in DB and clears session cookie.
    """
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1].strip()

    if token:
        destroy_session(token)

    response.delete_cookie("session_token")
    return {"status": "success", "message": "Logged out successfully."}


# User-Bound Saved Bookmarks API Endpoints

@saved_router.get("")
def get_user_saved_articles(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """
    Retrieves saved news bookmarks for the logged-in user.
    """
    if not current_user:
        return []

    user_id = current_user["user_id"]
    query = """
        SELECT article_url as url, title, source, published_at 
        FROM user_saved_articles 
        WHERE user_id = %s 
        ORDER BY saved_at DESC
    """
    articles = execute_query(query, (user_id,), fetchall=True)
    return articles or []


@saved_router.post("")
def save_user_article(payload: SaveArticleRequest, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """
    Saves a news article bookmark for the logged-in user.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required to save articles.")

    user_id = current_user["user_id"]
    query = """
        INSERT INTO user_saved_articles (user_id, article_url, title, source, published_at)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE title = VALUES(title), source = VALUES(source)
    """
    execute_query(query, (user_id, payload.url, payload.title, payload.source, payload.published_at), commit=True)
    return {"status": "success", "message": "Article saved successfully."}


@saved_router.delete("")
def delete_user_article(url: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """
    Removes a news article bookmark for the logged-in user.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")

    user_id = current_user["user_id"]
    query = "DELETE FROM user_saved_articles WHERE user_id = %s AND article_url = %s"
    execute_query(query, (user_id, url), commit=True)
    return {"status": "success", "message": "Article bookmark removed."}

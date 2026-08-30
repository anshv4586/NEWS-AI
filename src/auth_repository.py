"""
Authentication & Client Database Repository for Global News AI

Manages user registration, secure salted password hashing, credential verification,
and persistent client storage in the 'client_db' table across MySQL and SQLite fallback.
"""

from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json
import logging
import os
import secrets
from datetime import datetime
from src.database import get_connection, execute_query

logger = logging.getLogger(__name__)

SALT_LENGTH = 16


def _hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Computes secure salted SHA-256 password hash.
    Returns (password_hash_with_salt, salt).
    Format stored in DB: salt$hash
    """
    if not salt:
        salt = secrets.token_hex(SALT_LENGTH)
    
    hash_obj = hashlib.sha256(f"{salt}{password}".encode("utf-8"))
    pwd_hash = hash_obj.hexdigest()
    return f"{salt}${pwd_hash}", salt


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a plaintext password against the stored salt$hash format."""
    if not stored_hash or "$" not in stored_hash:
        return False
    salt, _ = stored_hash.split("$", 1)
    computed_hash, _ = _hash_password(password, salt=salt)
    return computed_hash == stored_hash


def init_client_db():
    """
    Initializes the 'client_db' table in the active database engine (MySQL or SQLite).
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS client_db (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        country VARCHAR(100) DEFAULT 'Global',
        preferences TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login_at DATETIME
    );
    """
    try:
        execute_query(create_table_sql, commit=True)
        logger.info("[Auth Repository] 'client_db' table schema verified/initialized successfully.")
    except Exception as err:
        # Retry with standard SQLite syntax if AUTO_INCREMENT triggers syntax variance
        sqlite_table_sql = """
        CREATE TABLE IF NOT EXISTS client_db (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            country VARCHAR(100) DEFAULT 'Global',
            preferences TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login_at DATETIME
        );
        """
        try:
            execute_query(sqlite_table_sql, commit=True)
            logger.info("[Auth Repository] 'client_db' table initialized with fallback SQLite schema.")
        except Exception as sql_err:
            logger.error(f"[Auth Repository] Failed to initialize 'client_db': {sql_err}")


def register_client(
    name: str,
    email: str,
    password: str,
    country: str = "Global",
    preferences: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Registers a new client and persists their record into 'client_db'.
    Returns (success: bool, message: str, client_profile: Optional[dict]).
    """
    clean_name = (name or "").strip()
    clean_email = (email or "").strip().lower()
    clean_pwd = (password or "").strip()
    clean_country = (country or "Global").strip()

    if not clean_name or len(clean_name) < 2:
        return False, "Name must be at least 2 characters long.", None

    if not clean_email or "@" not in clean_email or "." not in clean_email:
        return False, "Please provide a valid email address.", None

    if not clean_pwd or len(clean_pwd) < 6:
        return False, "Password must be at least 6 characters long.", None

    # Check if email is already registered in client_db
    existing = get_client_by_email(clean_email)
    if existing:
        return False, "An account with this email already exists. Please log in.", None

    pwd_hash, _ = _hash_password(clean_pwd)
    prefs_json = json.dumps(preferences or {"theme": "dark", "language": "English"}, ensure_ascii=False)
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    insert_sql = """
    INSERT INTO client_db (name, email, password_hash, country, preferences, created_at, last_login_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    try:
        execute_query(
            insert_sql,
            (clean_name, clean_email, pwd_hash, clean_country, prefs_json, now_str, now_str),
            commit=True,
        )
        created_client = get_client_by_email(clean_email)
        logger.info(f"[Auth Repository] Registered new client: {clean_email} (ID: {created_client.get('id') if created_client else 'N/A'})")
        return True, "Account created successfully.", created_client
    except Exception as err:
        logger.error(f"[Auth Repository] Error registering client '{clean_email}': {err}")
        return False, f"Registration failed: {err}", None


def authenticate_client(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticates a client against 'client_db'.
    Updates last_login_at timestamp upon successful verification.
    Returns (success: bool, message: str, client_profile: Optional[dict]).
    """
    clean_email = (email or "").strip().lower()
    clean_pwd = (password or "").strip()

    if not clean_email or not clean_pwd:
        return False, "Email and password are required.", None

    client_record = None
    try:
        query = "SELECT * FROM client_db WHERE LOWER(email) = LOWER(%s) LIMIT 1;"
        client_record = execute_query(query, (clean_email,), fetchone=True)
    except Exception as err:
        logger.error(f"[Auth Repository] Database error during authentication: {err}")
        return False, "Authentication service error. Please try again.", None

    if not client_record:
        return False, "Invalid email or password.", None

    stored_hash = client_record.get("password_hash")
    if not stored_hash or not _verify_password(clean_pwd, stored_hash):
        return False, "Invalid email or password.", None

    # Update last_login_at
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    client_id = client_record.get("id")
    try:
        update_sql = "UPDATE client_db SET last_login_at = %s WHERE id = %s;"
        execute_query(update_sql, (now_str, client_id), commit=True)
    except Exception as err:
        logger.warning(f"[Auth Repository] Could not update last_login_at for client {client_id}: {err}")

    # Prepare safe profile dictionary without password_hash
    profile = {
        "id": client_record.get("id"),
        "name": client_record.get("name"),
        "email": client_record.get("email"),
        "country": client_record.get("country", "Global"),
        "preferences": client_record.get("preferences"),
        "created_at": str(client_record.get("created_at")),
        "last_login_at": now_str,
    }
    return True, "Login successful.", profile


def get_client_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves safe client profile by email from 'client_db'."""
    clean_email = (email or "").strip().lower()
    try:
        query = "SELECT id, name, email, country, preferences, created_at, last_login_at FROM client_db WHERE LOWER(email) = LOWER(%s) LIMIT 1;"
        return execute_query(query, (clean_email,), fetchone=True)
    except Exception as err:
        logger.error(f"[Auth Repository] Error finding client by email: {err}")
        return None


def get_client_by_id(client_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves safe client profile by numeric ID from 'client_db'."""
    try:
        query = "SELECT id, name, email, country, preferences, created_at, last_login_at FROM client_db WHERE id = %s LIMIT 1;"
        return execute_query(query, (client_id,), fetchone=True)
    except Exception as err:
        logger.error(f"[Auth Repository] Error finding client by id: {err}")
        return None


def get_all_clients(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves all registered clients from 'client_db' (ordered by latest registration)."""
    try:
        query = "SELECT id, name, email, country, preferences, created_at, last_login_at FROM client_db ORDER BY id DESC LIMIT %s;"
        rows = execute_query(query, (limit,), fetchall=True)
        return rows or []
    except Exception as err:
        logger.error(f"[Auth Repository] Error fetching all clients: {err}")
        return []

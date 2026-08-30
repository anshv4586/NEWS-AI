"""
Database Module for Global News AI

Handles MySQL connection management with seamless SQLite fallback,
loading configuration securely from .env and providing error-isolated database access.
"""

import os
import sqlite3
import re
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Track database driver mode: 'mysql' or 'sqlite'
_ACTIVE_DRIVER: Optional[str] = None
_SQLITE_PATH: Optional[Path] = None


import tempfile

def get_sqlite_path() -> Path:
    """Returns persistent SQLite file path, using /tmp or temp dir in serverless or data/ locally."""
    global _SQLITE_PATH
    if _SQLITE_PATH is None:
        # In serverless environments (like Vercel / AWS Lambda), only /tmp is writable
        if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            tmp_dir = Path("/tmp") if (Path("/tmp").exists() and os.name != "nt") else Path(tempfile.gettempdir())
            tmp_dir.mkdir(parents=True, exist_ok=True)
            _SQLITE_PATH = tmp_dir / "global_news.db"
        else:
            data_dir = Path(__file__).resolve().parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            _SQLITE_PATH = data_dir / "global_news.db"
    return _SQLITE_PATH


def _init_sqlite_schema(conn: sqlite3.Connection):
    """Initializes schema tables in SQLite if they do not exist."""
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            url TEXT NOT NULL UNIQUE,
            source TEXT NOT NULL,
            published_at TEXT,
            author TEXT,
            category TEXT DEFAULT 'General',
            language TEXT DEFAULT 'English',
            country TEXT DEFAULT 'Global',
            keywords TEXT,
            quality_status TEXT DEFAULT 'valid',
            embedding_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            phone TEXT UNIQUE,
            auth_type TEXT NOT NULL DEFAULT 'email',
            is_verified INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS otp_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT NOT NULL,
            auth_type TEXT NOT NULL DEFAULT 'email',
            otp_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            resend_count INTEGER DEFAULT 0,
            is_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            user_id TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            user_agent TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_saved_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            article_url TEXT NOT NULL,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            published_at TEXT,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, article_url)
        );

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
    """)
    conn.commit()
    cursor.close()


def get_db_config() -> Dict[str, Any]:
    """
    Retrieves MySQL configuration parameters from environment variables.
    """
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "database": os.getenv("DB_NAME", "global_news"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "autocommit": False,
        "connection_timeout": 2,
    }


class SQLiteCursorWrapper:
    """Wrapper around sqlite3.Cursor to provide MySQL-compatible dict cursor behavior."""
    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    def execute(self, sql: str, params: Optional[Union[tuple, list]] = None):
        # Translate MySQL query syntax to SQLite
        sqlite_sql = _translate_sql_for_sqlite(sql)
        # Convert params to list/tuple
        exec_params = params or ()
        return self._cursor.execute(sqlite_sql, exec_params)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(r) for r in rows]

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        self._cursor.close()


class SQLiteConnectionWrapper:
    """Wrapper around sqlite3.Connection to provide MySQL-like interface."""
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def cursor(self, dictionary: bool = True):
        cur = self._conn.cursor()
        return SQLiteCursorWrapper(cur)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def is_connected(self):
        return True


def _translate_sql_for_sqlite(sql: str) -> str:
    """Translates MySQL-specific SQL statements to SQLite equivalents."""
    s = sql

    # Replace %s parameter placeholder with ?
    s = re.sub(r'(?<!%)(%s)', '?', s)

    # Replace INSERT IGNORE INTO -> INSERT OR IGNORE INTO
    s = re.sub(r'\bINSERT\s+IGNORE\s+INTO\b', 'INSERT OR IGNORE INTO', s, flags=re.IGNORECASE)

    # Replace ON DUPLICATE KEY UPDATE with SQLite ON CONFLICT DO UPDATE
    if "ON DUPLICATE KEY UPDATE" in s.upper():
        if "user_saved_articles" in s:
            s = re.sub(
                r'ON\s+DUPLICATE\s+KEY\s+UPDATE.*',
                'ON CONFLICT(user_id, article_url) DO UPDATE SET title=excluded.title, source=excluded.source',
                s,
                flags=re.IGNORECASE
            )

    # Replace CURDATE() with date('now')
    s = re.sub(r'\bCURDATE\(\)', "date('now')", s, flags=re.IGNORECASE)

    # Replace NOW() - INTERVAL ? HOUR with datetime('now', '-' || ? || ' hours')
    s = re.sub(
        r'NOW\(\)\s*-\s*INTERVAL\s*(\?|\d+)\s*HOUR',
        r"datetime('now', '-' || \1 || ' hours')",
        s,
        flags=re.IGNORECASE
    )

    # Replace AUTO_INCREMENT with AUTOINCREMENT
    s = re.sub(r'\bAUTO_INCREMENT\b', 'AUTOINCREMENT', s, flags=re.IGNORECASE)

    # Replace NOW() with datetime('now')
    s = re.sub(r'\bNOW\(\)', "datetime('now')", s, flags=re.IGNORECASE)

    return s


def get_sqlite_connection() -> SQLiteConnectionWrapper:
    """Creates and returns SQLite connection with schema initialized."""
    db_file = get_sqlite_path()
    conn = sqlite3.connect(str(db_file), timeout=10.0)
    conn.row_factory = sqlite3.Row
    _init_sqlite_schema(conn)
    return SQLiteConnectionWrapper(conn)


def get_connection():
    """
    Establishes and returns an active database connection.
    Attempts MySQL first; if unavailable, seamlessly uses SQLite.
    Caches driver selection so subsequent calls do not experience socket connection delays.
    """
    global _ACTIVE_DRIVER
    
    # Fast path: If driver is already determined to be SQLite, return instantly
    if _ACTIVE_DRIVER == "sqlite":
        return get_sqlite_connection()

    config = get_db_config()
    host = (config.get("host") or "").strip()

    # In serverless/Vercel with localhost or unconfigured host, immediately use SQLite
    if (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")) and host in ("localhost", "127.0.0.1", ""):
        _ACTIVE_DRIVER = "sqlite"
        return get_sqlite_connection()

    try:
        import mysql.connector
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            _ACTIVE_DRIVER = "mysql"
            return connection
    except Exception as e:
        logger.info(f"MySQL unavailable ({e}). Using embedded SQLite database fallback.")
        _ACTIVE_DRIVER = "sqlite"
        return get_sqlite_connection()

    _ACTIVE_DRIVER = "sqlite"
    return get_sqlite_connection()


def test_connection() -> bool:
    """
    Utility function to test database connectivity.
    Returns True if either MySQL or SQLite connection succeeds.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        res = cur.fetchone()
        cur.close()
        conn.close()
        return res is not None
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def execute_query(
    sql: str,
    params: Optional[tuple] = None,
    fetchone: bool = False,
    fetchall: bool = False,
    commit: bool = False,
    dictionary: bool = True,
):
    """
    Executes a SQL query with parameter binding, automatic connection release,
    and dictionary output formatting across both MySQL and SQLite.
    """
    conn = None
    try:
        conn = get_connection()
    except Exception as err:
        logger.warning(f"Database connection unavailable: {err}")
        return None if (fetchone or commit) else []

    try:
        cursor = conn.cursor(dictionary=dictionary) if hasattr(conn, "cursor") else conn.cursor()
        cursor.execute(sql, params or ())
        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()

        if commit:
            conn.commit()

        cursor.close()
        return result
    except Exception as e:
        if conn and hasattr(conn, "rollback"):
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"SQL execution error: {e} | Query: {sql}")
        return None if (fetchone or commit) else []
    finally:
        if conn and hasattr(conn, "close"):
            try:
                conn.close()
            except Exception:
                pass




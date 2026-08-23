"""
Database Module for Global News AI

Handles MySQL connection management, loading configuration securely from .env,
and providing error-isolated database access.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, MySQLConnection

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


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
    }


def get_connection() -> MySQLConnection:
    """
    Establishes and returns an active MySQL database connection.
    Raises Exception if connection fails (masking credentials for security).
    """
    config = get_db_config()
    try:
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            return connection
        else:
            raise Error("Connection object created but is_connected() returned False.")
    except Error as e:
        safe_user = config.get("user", "unknown")
        safe_host = config.get("host", "localhost")
        safe_db = config.get("database", "global_news")
        logger.error(
            f"Failed to connect to MySQL [{safe_user}@{safe_host}:{config.get('port')}/{safe_db}]: {e}"
        )
        raise ConnectionError(f"Database connection error: {e}") from e


def test_connection() -> bool:
    """
    Utility function to test Python -> MySQL connectivity.
    Returns True if connection succeeds, False otherwise.
    """
    try:
        conn = get_connection()
        db_info = conn.server_info

        logger.info(f"Successfully connected to MySQL Server version {db_info}")
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        current_db = cursor.fetchone()
        logger.info(f"Active Database: {current_db[0] if current_db else 'None'}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"MySQL connection test failed: {e}")
        return False

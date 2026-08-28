"""
Authentication Service & Security Module for Global News AI

Handles OTP generation, SHA-256 salted hashing, rate limiting,
email/SMS delivery (with dev logger fallback), session creation,
and HTTP-only cookie authentication.
"""

import os
import re
import uuid
import secrets
import hashlib
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from src.database import execute_query

logger = logging.getLogger(__name__)

# Constants
OTP_EXPIRATION_MINUTES = 5
OTP_MAX_ATTEMPTS = 5
RATE_LIMIT_MINUTES = 10
MAX_OTP_REQUESTS_PER_WINDOW = 3
SESSION_EXPIRATION_DAYS = 7


def hash_otp(plain_otp: str, salt: str) -> str:
    """
    Computes a secure SHA-256 salted hash of the plain OTP string.
    """
    combined = f"{salt}:{plain_otp}".encode('utf-8')
    return hashlib.sha256(combined).hexdigest()


def generate_otp() -> Tuple[str, str, str]:
    """
    Generates a 6-digit plain OTP, a random salt, and the computed OTP hash.
    Returns: (plain_otp, salt, otp_hash)
    """
    plain_otp = f"{secrets.randbelow(900000) + 100000:06d}"
    salt = secrets.token_hex(16)
    otp_hash = hash_otp(plain_otp, salt)
    return plain_otp, salt, otp_hash


def normalize_identifier(identifier: str, auth_type: str, country_code: str = "+91") -> str:
    """
    Validates and normalizes email addresses or phone numbers into standardized formats.
    """
    clean_id = (identifier or "").strip()
    if not clean_id:
        raise ValueError("Identifier cannot be empty.")

    if auth_type == "email":
        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_pattern, clean_id):
            raise ValueError("Invalid email address format.")
        return clean_id.lower()

    elif auth_type == "phone":
        # Remove spaces, dashes, and parentheses
        digits = re.sub(r"[^\d+]", "", clean_id)
        if not digits:
            raise ValueError("Invalid phone number format.")
        
        # Prepend country code if missing leading '+'
        if not digits.startswith("+"):
            cc = country_code.strip()
            if not cc.startswith("+"):
                cc = f"+{cc}"
            digits = f"{cc}{digits.lstrip('0')}"

        if len(digits) < 8 or len(digits) > 16:
            raise ValueError("Phone number must be between 8 and 15 digits including country code.")

        return digits
    else:
        raise ValueError("Invalid authentication type. Must be 'email' or 'phone'.")


def send_otp_delivery(identifier: str, auth_type: str, plain_otp: str):
    """
    Delivers plain OTP via configured SMTP (Email) or Twilio (SMS).
    Falls back to Development Logger if provider environment variables are not set.
    """
    if auth_type == "email":
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("SMTP_FROM_EMAIL", smtp_user or "noreply@newsai.com")

        if smtp_host and smtp_user and smtp_pass:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"Your Global News AI Verification Code: {plain_otp}"
                msg["From"] = from_email
                msg["To"] = identifier

                text = f"Your Global News AI OTP code is: {plain_otp}. It expires in 5 minutes."
                html = f"""
                <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 24px; background: #141417; color: #f0f0f3; border-radius: 16px; border: 1px solid #e5ad67;">
                    <h2 style="color: #e5ad67; margin-top: 0;">Global News AI</h2>
                    <p style="font-size: 16px; color: #d0d0d8;">Use the verification code below to complete your login:</p>
                    <div style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #e5ad67; background: #1c1c22; padding: 16px; text-align: center; border-radius: 12px; margin: 20px 0;">
                        {plain_otp}
                    </div>
                    <p style="font-size: 14px; color: #909098;">This code will expire in 5 minutes. If you did not request this code, please ignore this email.</p>
                </div>
                """
                msg.attach(MIMEText(text, "plain"))
                msg.attach(MIMEText(html, "html"))

                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(from_email, [identifier], msg.as_string())
                
                logger.info(f"Successfully sent OTP email to {identifier}")
                return
            except Exception as err:
                logger.error(f"Failed to send SMTP email to {identifier}: {err}")
    
    elif auth_type == "phone":
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")

        if twilio_sid and twilio_token and twilio_phone:
            try:
                from twilio.rest import Client
                client = Client(twilio_sid, twilio_token)
                client.messages.create(
                    body=f"Your Global News AI verification code is {plain_otp}. Valid for 5 minutes.",
                    from_=twilio_phone,
                    to=identifier
                )
                logger.info(f"Successfully sent Twilio SMS OTP to {identifier}")
                return
            except Exception as err:
                logger.error(f"Failed to send Twilio SMS to {identifier}: {err}")

    # Fallback Development Logger for local testing
    logger.info("🔑 " + "=" * 64)
    logger.info(f"🔑 [DEV OTP LOGGER] Verification Code for {identifier} ({auth_type.upper()}): {plain_otp}")
    logger.info("🔑 " + "=" * 64)


def request_otp(identifier: str, auth_type: str, country_code: str = "+91") -> Tuple[bool, str]:
    """
    Generates, rate-limits, and sends a new OTP for the normalized identifier.
    """
    norm_id = normalize_identifier(identifier, auth_type, country_code)

    # 1. Rate Limiting Check: Max 3 requests in 10 minutes
    window_start = datetime.utcnow() - timedelta(minutes=RATE_LIMIT_MINUTES)
    rate_query = """
        SELECT COUNT(*) as request_count 
        FROM otp_verifications 
        WHERE identifier = %s AND created_at >= %s
    """
    rate_res = execute_query(rate_query, (norm_id, window_start), fetchone=True)
    if rate_res and rate_res.get("request_count", 0) >= MAX_OTP_REQUESTS_PER_WINDOW:
        return False, "Too many OTP requests. Please wait 10 minutes before requesting another code."

    # 2. Invalidate older unused OTPs for this identifier
    invalidate_query = """
        UPDATE otp_verifications 
        SET is_used = TRUE 
        WHERE identifier = %s AND is_used = FALSE
    """
    execute_query(invalidate_query, (norm_id,), commit=True)

    # 3. Generate new salted OTP hash & expiration timestamp
    plain_otp, salt, otp_hash = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRATION_MINUTES)

    # 4. Save record to DB
    insert_query = """
        INSERT INTO otp_verifications (identifier, auth_type, otp_hash, salt, expires_at)
        VALUES (%s, %s, %s, %s, %s)
    """
    execute_query(insert_query, (norm_id, auth_type, otp_hash, salt, expires_at), commit=True)

    # 5. Deliver via Provider or Dev Logger
    send_otp_delivery(norm_id, auth_type, plain_otp)

    return True, f"Verification code sent to {norm_id}."


def verify_otp(identifier: str, auth_type: str, plain_otp: str, country_code: str = "+91") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Verifies entered OTP against database hash, checks rate limits & expiration,
    and provisions user record upon success.
    Returns: (is_success, message, user_dict)
    """
    norm_id = normalize_identifier(identifier, auth_type, country_code)
    clean_otp = (plain_otp or "").strip()

    if len(clean_otp) != 6 or not clean_otp.isdigit():
        return False, "OTP must be a 6-digit numeric code.", None

    # Retrieve latest active OTP record for identifier
    select_query = """
        SELECT * FROM otp_verifications 
        WHERE identifier = %s AND is_used = FALSE 
        ORDER BY created_at DESC LIMIT 1
    """
    otp_record = execute_query(select_query, (norm_id,), fetchone=True)

    if not otp_record:
        return False, "No active verification code found. Please request a new code.", None

    # Check if expired
    expires_at = otp_record["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    
    if datetime.utcnow() > expires_at:
        execute_query("UPDATE otp_verifications SET is_used = TRUE WHERE id = %s", (otp_record["id"],), commit=True)
        return False, "Verification code has expired. Please request a new code.", None

    # Check maximum verification attempts
    attempts = otp_record.get("attempts", 0) + 1
    execute_query("UPDATE otp_verifications SET attempts = %s WHERE id = %s", (attempts, otp_record["id"]), commit=True)

    if attempts > OTP_MAX_ATTEMPTS:
        execute_query("UPDATE otp_verifications SET is_used = TRUE WHERE id = %s", (otp_record["id"],), commit=True)
        return False, "Too many failed attempts. This code is now invalid. Please request a new code.", None

    # Compute hash and compare
    expected_hash = hash_otp(clean_otp, otp_record["salt"])
    if expected_hash != otp_record["otp_hash"]:
        remaining = OTP_MAX_ATTEMPTS - attempts
        return False, f"Incorrect verification code. {remaining} attempt(s) remaining.", None

    # Mark OTP as used
    execute_query("UPDATE otp_verifications SET is_used = TRUE WHERE id = %s", (otp_record["id"],), commit=True)

    # Provision user record
    user = get_or_create_user(norm_id, auth_type)
    return True, "Verification successful.", user


def get_or_create_user(identifier: str, auth_type: str) -> Dict[str, Any]:
    """
    Retrieves existing user or creates a new user record in the users table.
    """
    if auth_type == "email":
        select_query = "SELECT * FROM users WHERE email = %s"
    else:
        select_query = "SELECT * FROM users WHERE phone = %s"

    user = execute_query(select_query, (identifier,), fetchone=True)
    if user:
        return user

    # Create new user
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    if auth_type == "email":
        insert_query = "INSERT INTO users (user_id, email, auth_type) VALUES (%s, %s, %s)"
        execute_query(insert_query, (user_id, identifier, auth_type), commit=True)
    else:
        insert_query = "INSERT INTO users (user_id, phone, auth_type) VALUES (%s, %s, %s)"
        execute_query(insert_query, (user_id, identifier, auth_type), commit=True)

    new_user = execute_query("SELECT * FROM users WHERE user_id = %s", (user_id,), fetchone=True)
    return new_user


def create_session(user_id: str, user_agent: Optional[str] = None, ip_address: Optional[str] = None) -> Tuple[str, datetime]:
    """
    Generates a secure session token and persists session to DB.
    Returns: (session_id, expires_at)
    """
    session_id = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(days=SESSION_EXPIRATION_DAYS)

    insert_query = """
        INSERT INTO sessions (session_id, user_id, expires_at, user_agent, ip_address)
        VALUES (%s, %s, %s, %s, %s)
    """
    execute_query(insert_query, (session_id, user_id, expires_at, user_agent, ip_address), commit=True)
    return session_id, expires_at


def get_user_from_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Validates session token and returns associated user dictionary if valid and unexpired.
    """
    if not session_id or not session_id.strip():
        return None

    query = """
        SELECT u.*, s.expires_at as session_expires_at
        FROM sessions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.session_id = %s AND s.expires_at > %s
    """
    user = execute_query(query, (session_id.strip(), datetime.utcnow()), fetchone=True)
    return user


def destroy_session(session_id: str):
    """
    Invalidates session by deleting it from DB.
    """
    if session_id:
        execute_query("DELETE FROM sessions WHERE session_id = %s", (session_id,), commit=True)

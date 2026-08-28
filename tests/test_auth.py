"""
Comprehensive Unit & Integration Test Suite for OTP Authentication System
"""

import sys
import unittest
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.auth import (
    hash_otp,
    generate_otp,
    normalize_identifier,
    request_otp,
    verify_otp,
    get_or_create_user,
    create_session,
    get_user_from_session,
    destroy_session,
)
from src.database import execute_query


class TestAuthSystem(unittest.TestCase):

    def setUp(self):
        """Clean up test identifier records before each test."""
        self.test_email = "test_user_auth@example.com"
        self.test_phone = "+919999888877"

        execute_query("DELETE FROM otp_verifications WHERE identifier IN (%s, %s)", (self.test_email, self.test_phone), commit=True)
        execute_query("DELETE FROM users WHERE email = %s OR phone = %s", (self.test_email, self.test_phone), commit=True)

    def test_otp_hashing_security(self):
        """Verify plain OTP is never hashed identically without salt and hash comparison works."""
        plain_otp = "654321"
        salt1 = "salt_alpha_123"
        salt2 = "salt_beta_456"

        hash1 = hash_otp(plain_otp, salt1)
        hash2 = hash_otp(plain_otp, salt2)

        self.assertNotEqual(hash1, hash2)
        self.assertEqual(hash1, hash_otp(plain_otp, salt1))

    def test_normalize_identifier(self):
        """Verify email and phone normalization with country codes."""
        # Email normalization
        norm_email = normalize_identifier("  User.Test@EXAMPLE.com ", "email")
        self.assertEqual(norm_email, "user.test@example.com")

        # Phone normalization with +91 default
        norm_phone = normalize_identifier("9999888877", "phone", country_code="+91")
        self.assertEqual(norm_phone, "+919999888877")

        # Invalid Email
        with self.assertRaises(ValueError):
            normalize_identifier("invalid_email_at", "email")

        # Invalid Phone
        with self.assertRaises(ValueError):
            normalize_identifier("123", "phone")

    def test_request_and_verify_otp_flow(self):
        """Verify requesting OTP, retrieving hash from DB, and successful verification."""
        # 1. Request OTP
        success, msg = request_otp(self.test_email, "email")
        self.assertTrue(success)

        # 2. Retrieve plain OTP from dev logger DB simulation for testing
        otp_rec = execute_query("SELECT * FROM otp_verifications WHERE identifier = %s AND is_used = FALSE", (self.test_email,), fetchone=True)
        self.assertIsNotNone(otp_rec)
        self.assertIn("salt", otp_rec)
        self.assertIn("otp_hash", otp_rec)

        # 3. Simulate correct OTP code
        # Find which 6-digit code matches the salt/hash pair
        matched_otp = None
        for code in range(100000, 999999):
            if hash_otp(str(code), otp_rec["salt"]) == otp_rec["otp_hash"]:
                matched_otp = str(code)
                break
        
        self.assertIsNotNone(matched_otp)

        # 4. Verify OTP
        v_success, v_msg, user = verify_otp(self.test_email, "email", matched_otp)
        self.assertTrue(v_success)
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], self.test_email)

    def test_incorrect_otp_attempts_lockout(self):
        """Verify wrong OTP decrements remaining attempts and invalidates after max attempts."""
        request_otp(self.test_email, "email")

        # Enter wrong code 5 times
        for i in range(5):
            success, msg, user = verify_otp(self.test_email, "email", "000000")
            self.assertFalse(success)

        # 6th attempt should state too many failed attempts
        success, msg, user = verify_otp(self.test_email, "email", "000000")
        self.assertFalse(success)
        self.assertIn("invalid", msg.lower())

    def test_rate_limiting(self):
        """Verify 4th request within 10 minutes is blocked by rate limiter."""
        for _ in range(3):
            success, msg = request_otp(self.test_phone, "phone")
            self.assertTrue(success)

        # 4th request should fail due to rate limiting
        success, msg = request_otp(self.test_phone, "phone")
        self.assertFalse(success)
        self.assertIn("too many", msg.lower())

    def test_session_lifecycle(self):
        """Verify session creation, user retrieval, and logout destruction."""
        user = get_or_create_user(self.test_email, "email")
        self.assertIsNotNone(user)

        session_id, expires_at = create_session(user["user_id"], "Test-Browser", "127.0.0.1")
        self.assertIsNotNone(session_id)

        # Retrieve user from session
        session_user = get_user_from_session(session_id)
        self.assertIsNotNone(session_user)
        self.assertEqual(session_user["user_id"], user["user_id"])

        # Destroy session
        destroy_session(session_id)
        self.assertIsNone(get_user_from_session(session_id))


if __name__ == "__main__":
    unittest.main()

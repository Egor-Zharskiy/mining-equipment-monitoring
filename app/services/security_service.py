import base64
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.config import auth_config


class SecurityService:
    """Utility helpers for password hashing and JWT token handling."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using PBKDF2-HMAC with a random salt."""

        salt = os.urandom(16)
        derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return f"{base64.b64encode(salt).decode()}${base64.b64encode(derived_key).decode()}"

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a plain password against a stored PBKDF2-HMAC hash."""

        try:
            encoded_salt, encoded_hash = hashed_password.split("$", maxsplit=1)
        except ValueError:
            return False

        salt = base64.b64decode(encoded_salt.encode())
        expected_hash = base64.b64decode(encoded_hash.encode())
        candidate_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(candidate_hash, expected_hash)

    @staticmethod
    def create_access_token(*, user_id: UUID) -> str:
        """Create a signed JWT access token for the provided user."""

        expires_at = datetime.now(UTC) + timedelta(minutes=auth_config.access_token_expire_minutes)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": expires_at,
        }
        return jwt.encode(payload, auth_config.secret_key, algorithm=auth_config.algorithm)

    @staticmethod
    def decode_access_token(token: str) -> dict:
        """Decode and validate a JWT access token."""

        return jwt.decode(token, auth_config.secret_key, algorithms=[auth_config.algorithm])

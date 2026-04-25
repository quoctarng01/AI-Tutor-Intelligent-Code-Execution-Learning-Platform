"""
Unit tests for JWT authentication and security.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from jose import jwt

from backend.security import (
    TokenService,
    TokenData,
    TokenPair,
    hash_password,
    verify_password,
)
from backend.config import settings


class TestTokenService:
    """Tests for TokenService."""

    def test_create_access_token(self):
        """Test creating an access token."""
        token = TokenService.create_access_token(
            username="test_user",
            session_id="session_123",
            group_type="tutor",
        )

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        assert payload["sub"] == "test_user"
        assert payload["session_id"] == "session_123"
        assert payload["group_type"] == "tutor"
        assert payload["type"] == "access"

    def test_create_access_token_with_custom_expiry(self):
        """Test creating an access token with custom expiry."""
        expires = timedelta(minutes=30)
        token = TokenService.create_access_token(
            username="test_user",
            session_id="session_123",
            group_type="tutor",
            expires_delta=expires,
        )

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        # Token should expire within 31 minutes (30 + 1 minute buffer)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        assert (exp_time - now).total_seconds() < 31 * 60

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        token = TokenService.create_refresh_token(
            username="test_user",
            session_id="session_123",
        )

        assert token is not None
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        assert payload["sub"] == "test_user"
        assert payload["session_id"] == "session_123"
        assert payload["type"] == "refresh"

    def test_create_token_pair(self):
        """Test creating both access and refresh tokens."""
        tokens = TokenService.create_token_pair(
            username="test_user",
            session_id="session_123",
            group_type="tutor",
        )

        assert isinstance(tokens, TokenPair)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in == settings.access_token_expire_minutes * 60

    def test_verify_access_token(self):
        """Test verifying a valid access token."""
        token = TokenService.create_access_token(
            username="test_user",
            session_id="session_123",
            group_type="tutor",
        )

        token_data = TokenService.verify_token(token, token_type="access")

        assert token_data.sub == "test_user"
        assert token_data.session_id == "session_123"
        assert token_data.group_type == "tutor"
        assert token_data.type == "access"

    def test_verify_refresh_token(self):
        """Test verifying a valid refresh token."""
        token = TokenService.create_refresh_token(
            username="test_user",
            session_id="session_123",
        )

        token_data = TokenService.verify_token(token, token_type="refresh")

        assert token_data.sub == "test_user"
        assert token_data.session_id == "session_123"
        assert token_data.type == "refresh"

    def test_verify_token_wrong_type(self):
        """Test that verifying token with wrong type raises error."""
        from fastapi import HTTPException

        token = TokenService.create_access_token(
            username="test_user",
            session_id="session_123",
            group_type="tutor",
        )

        with pytest.raises(HTTPException) as exc_info:
            TokenService.verify_token(token, token_type="refresh")

        assert exc_info.value.status_code == 401
        assert "Invalid token type" in str(exc_info.value.detail)

    def test_verify_expired_token(self):
        """Test that expired tokens are rejected."""
        from fastapi import HTTPException

        # Create token that expired 1 hour ago
        expired_token = jwt.encode(
            {
                "sub": "test_user",
                "session_id": "session_123",
                "group_type": "tutor",
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
                "type": "access",
            },
            settings.secret_key,
            algorithm=settings.algorithm,
        )

        with pytest.raises(HTTPException) as exc_info:
            TokenService.verify_token(expired_token, token_type="access")

        assert exc_info.value.status_code == 401

    def test_verify_invalid_token(self):
        """Test that invalid tokens are rejected."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            TokenService.verify_token("invalid.token.here", token_type="access")

        assert exc_info.value.status_code == 401

    def test_verify_token_wrong_secret(self):
        """Test that tokens signed with wrong secret are rejected."""
        from fastapi import HTTPException

        # Create token with different secret
        wrong_token = jwt.encode(
            {
                "sub": "test_user",
                "session_id": "session_123",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
                "type": "access",
            },
            "wrong-secret-key",
            algorithm=settings.algorithm,
        )

        with pytest.raises(HTTPException) as exc_info:
            TokenService.verify_token(wrong_token, token_type="access")

        assert exc_info.value.status_code == 401


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "secure_password_123"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "secure_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        password = "secure_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "secure_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestTokenData:
    """Tests for TokenData model."""

    def test_token_data_creation(self):
        """Test creating TokenData."""
        data = TokenData(
            sub="test_user",
            session_id="session_123",
            group_type="tutor",
        )

        assert data.sub == "test_user"
        assert data.session_id == "session_123"
        assert data.group_type == "tutor"
        assert data.type == "access"  # Default

    def test_token_data_with_expiry(self):
        """Test creating TokenData with expiry."""
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        data = TokenData(
            sub="test_user",
            session_id="session_123",
            group_type="tutor",
            exp=exp,
        )

        assert data.exp == exp

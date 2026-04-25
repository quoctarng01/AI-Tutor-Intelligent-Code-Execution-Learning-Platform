"""
Security module for JWT authentication and authorization.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from backend.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security scheme
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Token payload data."""
    sub: str  # Subject (user/session identifier)
    session_id: str
    group_type: str
    exp: datetime | None = None
    type: str = "access"  # "access" or "refresh"


class TokenPair(BaseModel):
    """Pair of access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenService:
    """Service for creating and validating JWT tokens."""

    @staticmethod
    def create_access_token(
        username: str,
        session_id: str,
        group_type: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a new access token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode = {
            "sub": username,
            "session_id": session_id,
            "group_type": group_type,
            "exp": expire,
            "type": "access",
            "iat": datetime.now(timezone.utc),
        }
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        username: str,
        session_id: str,
    ) -> str:
        """Create a new refresh token with longer expiry."""
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
        to_encode = {
            "sub": username,
            "session_id": session_id,
            "exp": expire,
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
        }
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        return encoded_jwt

    @staticmethod
    def create_token_pair(
        username: str,
        session_id: str,
        group_type: str,
    ) -> TokenPair:
        """Create both access and refresh tokens."""
        access_token = TokenService.create_access_token(
            username=username,
            session_id=session_id,
            group_type=group_type,
        )
        refresh_token = TokenService.create_refresh_token(
            username=username,
            session_id=session_id,
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> TokenData:
        """Verify and decode a token."""
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            token_data = TokenData(
                sub=payload.get("sub", ""),
                session_id=payload.get("session_id", ""),
                group_type=payload.get("group_type", ""),
                exp=datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc),
                type=payload.get("type", "access"),
            )
            return token_data
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Dependency for getting current user from token
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> TokenData:
    """
    Dependency that extracts and validates the JWT token from request.
    Raises 401 if token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenService.verify_token(credentials.credentials)


# Dependency for optional authentication (doesn't fail if no token)
async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> TokenData | None:
    """Optional authentication - returns None if no token provided."""
    if credentials is None:
        return None
    try:
        return TokenService.verify_token(credentials.credentials)
    except HTTPException:
        return None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

"""
Authentication and session management with JWT tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Session
from backend.schemas import SessionResponse, SessionStartRequest, TokenPair
from backend.security import (
    TokenService,
    get_current_user,
    TokenData,
)
from backend.services.rate_limiter import get_rate_limiter, RateLimiter
from backend.services.cache_service import get_cache_service
from backend.services.logging_service import get_logger
from backend.exceptions import UnauthorizedError, RateLimitError
from backend.config import settings


router = APIRouter(prefix="/session", tags=["auth"])
logger = get_logger("auth")


@router.post(
    "/start",
    response_model=SessionResponse,
    summary="Start a new student session",
    description="Creates a new student session and returns JWT tokens for authentication.",
    responses={
        201: {"description": "Session created successfully"},
        400: {"description": "Invalid request data"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def start_session(
    payload: SessionStartRequest,
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> SessionResponse:
    """Start a new tutoring session for a student."""
    # Check rate limit
    client_id = f"session_start:{payload.username}"
    is_allowed, _ = await rate_limiter.increment(client_id, "global", window_seconds=60)
    if not is_allowed:
        raise RateLimitError(retry_after=60)

    # Validate group type
    if payload.group_type not in ("tutor", "control"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group type. Must be 'tutor' or 'control'",
        )

    # Create session in database
    try:
        result = await db.execute(
            text("""
                INSERT INTO sessions (username, group_type)
                VALUES (:username, :group_type)
                RETURNING id, username, group_type, started_at
            """),
            {"username": payload.username, "group_type": payload.group_type}
        )
        row = result.fetchone()
        await db.commit()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session",
            )

        session_id = str(row[0])
        username = row[1]
        group_type = row[2]
        started_at = row[3]

        # Create JWT tokens
        tokens = TokenService.create_token_pair(
            username=username,
            session_id=session_id,
            group_type=group_type,
        )

        # Cache the session for quick lookup
        cache = get_cache_service()
        await cache.set(
            f"session:{session_id}",
            {"username": username, "group_type": group_type},
            ttl=3600 * 24,  # 24 hours
        )

        logger.info(
            "session_started",
            username=username,
            group_type=group_type,
            session_id=session_id,
        )

        # Return session response with tokens
        return SessionResponse(
            id=row[0],
            username=username,
            group_type=group_type,
            started_at=started_at,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("session_creation_failed", username=payload.username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session",
        )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session details",
    description="Retrieve details for a specific session.",
    responses={
        200: {"description": "Session details"},
        404: {"description": "Session not found"},
    },
)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> SessionResponse:
    """Get session details (requires authentication)."""
    # Verify the user is accessing their own session or is authorized
    if current_user.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )

    # Try cache first
    cache = get_cache_service()
    cached = await cache.get(f"session:{session_id}")
    if cached:
        # Need to fetch full session from DB for started_at
        pass

    result = await db.execute(
        text("SELECT id, username, group_type, started_at FROM sessions WHERE id = :id"),
        {"id": session_id}
    )
    row = result.fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="session_not_found",
        )

    return SessionResponse(
        id=row[0],
        username=row[1],
        group_type=row[2],
        started_at=row[3],
    )


@router.post(
    "/token",
    response_model=TokenPair,
    summary="Get authentication tokens",
    description="Get JWT tokens for an existing session. Used for re-authentication.",
    responses={
        200: {"description": "Tokens generated successfully"},
        404: {"description": "Session not found"},
    },
)
async def get_tokens(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> TokenPair:
    """Get JWT tokens for an existing session."""
    # Rate limit token requests
    is_allowed, _ = await rate_limiter.increment(f"token:{session_id}", "global", window_seconds=60)
    if not is_allowed:
        raise RateLimitError(retry_after=60)

    result = await db.execute(
        text("SELECT username, group_type FROM sessions WHERE id = :id"),
        {"id": session_id}
    )
    row = result.fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="session_not_found",
        )

    return TokenService.create_token_pair(
        username=row[0],
        session_id=session_id,
        group_type=row[1],
    )


@router.post(
    "/refresh",
    response_model=dict,
    summary="Refresh access token",
    description="Get a new access token using a refresh token.",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Refresh access token using refresh token."""
    try:
        token_data = TokenService.verify_token(refresh_token, token_type="refresh")

        # Verify session still exists
        result = await db.execute(
            text("SELECT username, group_type FROM sessions WHERE id = :id"),
            {"id": token_data.session_id}
        )
        row = result.fetchone()

        if row is None:
            raise UnauthorizedError("Session no longer exists")

        # Create new access token
        new_access_token = TokenService.create_access_token(
            username=row[0],
            session_id=token_data.session_id,
            group_type=row[1],
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("token_refresh_failed", error=str(e))
        raise UnauthorizedError("Invalid refresh token")

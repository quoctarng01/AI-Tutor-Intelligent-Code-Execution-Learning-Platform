"""
Rate limiting service using in-memory storage with optional Redis backend.
"""

import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.config import settings
from backend.services.logging_service import get_logger


logger = get_logger("rate_limiter")


@dataclass
class RateLimitInfo:
    """Information about a rate limit."""
    limit: int
    remaining: int
    reset_at: float
    window_seconds: int


class StorageBackend(ABC):
    """Abstract backend for rate limit storage."""

    @abstractmethod
    async def get(self, key: str) -> tuple[int, float] | None:
        """Get count and reset time for key."""
        pass

    @abstractmethod
    async def increment(self, key: str, window_seconds: int) -> int:
        """Increment count for key and return new count."""
        pass

    @abstractmethod
    async def clear(self, key: str) -> None:
        """Clear rate limit for key."""
        pass


class InMemoryStorage(StorageBackend):
    """In-memory rate limit storage (per-process)."""

    def __init__(self):
        self._counts: dict[str, int] = defaultdict(int)
        self._resets: dict[str, float] = {}
        self._lock = None  # Simplified for in-memory

    async def get(self, key: str) -> tuple[int, float] | None:
        now = time.time()
        if key not in self._counts:
            return None
        reset_at = self._resets.get(key, now)
        if now > reset_at:
            # Window expired
            del self._counts[key]
            if key in self._resets:
                del self._resets[key]
            return None
        return self._counts[key], reset_at

    async def increment(self, key: str, window_seconds: int) -> int:
        now = time.time()
        reset_at = self._resets.get(key, now + window_seconds)

        if now > reset_at:
            # New window
            self._counts[key] = 1
            self._resets[key] = now + window_seconds
            return 1

        self._counts[key] += 1
        return self._counts[key]

    async def clear(self, key: str) -> None:
        if key in self._counts:
            del self._counts[key]
        if key in self._resets:
            del self._resets[key]


class RedisStorage(StorageBackend):
    """Redis-based rate limit storage for distributed deployments."""

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._client = None

    async def _get_client(self):
        """Lazy initialization of Redis client."""
        if self._client is None:
            import redis.asyncio as redis
            self._client = redis.from_url(self._redis_url, decode_responses=True)
        return self._client

    async def get(self, key: str) -> tuple[int, float] | None:
        try:
            client = await self._get_client()
            count = await client.get(f"rl:{key}:count")
            reset_at = await client.get(f"rl:{key}:reset")

            if count is None or reset_at is None:
                return None

            reset_time = float(reset_at)
            if time.time() > reset_time:
                await self.clear(key)
                return None

            return int(count), reset_time
        except Exception as e:
            logger.error("redis_rate_limit_error", operation="get", error=str(e))
            return None

    async def increment(self, key: str, window_seconds: int) -> int:
        try:
            client = await self._get_client()
            now = time.time()
            pipe = client.pipeline()
            pipe.incr(f"rl:{key}:count")
            pipe.expire(f"rl:{key}:count", window_seconds)
            pipe.setnx(f"rl:{key}:reset", now + window_seconds)
            pipe.expire(f"rl:{key}:reset", window_seconds)
            results = await pipe.execute()
            return results[0]
        except Exception as e:
            logger.error("redis_rate_limit_error", operation="increment", error=str(e))
            return 1

    async def clear(self, key: str) -> None:
        try:
            client = await self._get_client()
            await client.delete(f"rl:{key}:count", f"rl:{key}:reset")
        except Exception as e:
            logger.error("redis_rate_limit_error", operation="clear", error=str(e))


class RateLimiter:
    """
    Rate limiter with configurable limits per endpoint type.
    """

    def __init__(self, storage: StorageBackend | None = None):
        self._storage = storage or InMemoryStorage()
        self._limits = {
            "global": settings.rate_limit_per_minute,
            "llm": settings.rate_limit_llm_per_minute,
            "submit": settings.rate_limit_per_minute,
            "hint": settings.rate_limit_llm_per_minute,
        }

    def _get_key(self, identifier: str, limit_type: str) -> str:
        """Generate rate limit key."""
        return f"{limit_type}:{identifier}"

    async def check_limit(
        self,
        identifier: str,
        limit_type: str = "global",
        window_seconds: int = 60,
    ) -> RateLimitInfo:
        """
        Check if identifier is within rate limit.

        Returns RateLimitInfo with current status.
        """
        limit = self._limits.get(limit_type, self._limits["global"])
        key = self._get_key(identifier, limit_type)

        count, reset_at = await self._storage.get(key) or (0, time.time())

        remaining = max(0, limit - count)
        is_limited = count >= limit

        return RateLimitInfo(
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            window_seconds=window_seconds,
        )

    async def increment(
        self,
        identifier: str,
        limit_type: str = "global",
        window_seconds: int = 60,
    ) -> tuple[bool, RateLimitInfo]:
        """
        Increment rate limit counter and check if within limit.

        Returns (is_allowed, rate_limit_info).
        """
        limit = self._limits.get(limit_type, self._limits["global"])
        key = self._get_key(identifier, limit_type)

        count = await self._storage.increment(key, window_seconds)
        reset_at = time.time() + window_seconds

        remaining = max(0, limit - count)
        is_allowed = count <= limit

        info = RateLimitInfo(
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            window_seconds=window_seconds,
        )

        if not is_allowed:
            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier,
                limit_type=limit_type,
                count=count,
                limit=limit,
            )

        return is_allowed, info

    async def reset(self, identifier: str, limit_type: str = "global") -> None:
        """Reset rate limit for identifier."""
        key = self._get_key(identifier, limit_type)
        await self._storage.clear(key)


# Create rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _redis_url = settings.redis_url
        _is_memory = not _redis_url or _redis_url == "redis://localhost:6379/0" or _redis_url.startswith("memory://")
        if not _is_memory:
            storage = RedisStorage(_redis_url)
        else:
            storage = InMemoryStorage()
        _rate_limiter = RateLimiter(storage)
    return _rate_limiter


def rate_limit_key_func(request: Request) -> str:
    """Get identifier for rate limiting from request."""
    # Use X-Forwarded-For if behind proxy, otherwise client host
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# SlowAPI limiter instance for decorator-based rate limiting
limiter = Limiter(
    key_func=rate_limit_key_func,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    storage_uri=settings.redis_url if settings.redis_url != "redis://localhost:6379/0" else "memory://",
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors."""
    logger.warning(
        "rate_limit_exceeded",
        client=request.client.host if request.client else "unknown",
        path=request.url.path,
    )
    return Response(
        content='{"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests. Please try again later."}}',
        status_code=429,
        media_type="application/json",
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
        },
    )

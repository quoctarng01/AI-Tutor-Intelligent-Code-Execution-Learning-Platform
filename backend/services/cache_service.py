"""
Caching service with Redis backend and in-memory fallback.
"""

import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar, Generic
from functools import wraps

from backend.config import settings
from backend.services.logging_service import get_logger


logger = get_logger("cache")


T = TypeVar("T")


class CacheInterface(ABC):
    """Abstract cache interface."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class InMemoryCache(CacheInterface):
    """Simple in-memory cache implementation."""

    def __init__(self):
        self._cache: dict[str, tuple[Any, float | None]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            if key not in self._cache:
                return None
            value, expires_at = self._cache[key]
            if expires_at and asyncio.get_event_loop().time() > expires_at:
                del self._cache[key]
                return None
            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        async with self._lock:
            expires_at = None
            if ttl:
                expires_at = asyncio.get_event_loop().time() + ttl
            self._cache[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()

    async def exists(self, key: str) -> bool:
        value = await self.get(key)
        return value is not None


class RedisCache(CacheInterface):
    """Redis-based cache implementation for distributed deployments."""

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._client = None
        self._lock = asyncio.Lock()

    async def _get_client(self):
        """Lazy initialization of Redis client."""
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    import redis.asyncio as redis
                    self._client = redis.from_url(
                        self._redis_url,
                        decode_responses=True,
                    )
        return self._client

    async def get(self, key: str) -> Any | None:
        try:
            client = await self._get_client()
            value = await client.get(f"cache:{key}")
            if value is None:
                return None
            return json.loads(value)
        except json.JSONDecodeError:
            return value
        except Exception as e:
            logger.error("redis_cache_get_error", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        try:
            client = await self._get_client()
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            if ttl:
                await client.setex(f"cache:{key}", ttl, value)
            else:
                await client.set(f"cache:{key}", value)
        except Exception as e:
            logger.error("redis_cache_set_error", key=key, error=str(e))

    async def delete(self, key: str) -> None:
        try:
            client = await self._get_client()
            await client.delete(f"cache:{key}")
        except Exception as e:
            logger.error("redis_cache_delete_error", key=key, error=str(e))

    async def clear(self) -> None:
        try:
            client = await self._get_client()
            keys = await client.keys("cache:*")
            if keys:
                await client.delete(*keys)
        except Exception as e:
            logger.error("redis_cache_clear_error", error=str(e))

    async def exists(self, key: str) -> bool:
        try:
            client = await self._get_client()
            return await client.exists(f"cache:{key}") > 0
        except Exception as e:
            logger.error("redis_cache_exists_error", key=key, error=str(e))
            return False


class CacheService:
    """
    Main caching service with decorator support.
    """

    def __init__(self, backend: CacheInterface):
        self._backend = backend
        self._ttl = settings.cache_ttl_seconds

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: int | None = None,
    ) -> Any:
        """
        Get value from cache or compute and cache it.
        """
        cached = await self._backend.get(key)
        if cached is not None:
            logger.debug("cache_hit", key=key)
            return cached

        logger.debug("cache_miss", key=key)
        value = await factory() if asyncio.iscoroutinefunction(factory) else factory()
        await self._backend.set(key, value, ttl or self._ttl)
        return value

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        return await self._backend.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        await self._backend.set(key, value, ttl or self._ttl)

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        await self._backend.delete(key)

    async def invalidate_pattern(self, pattern: str) -> None:
        """
        Invalidate all keys matching pattern.
        Note: This is a best-effort operation and may not be efficient
        with in-memory cache.
        """
        logger.info("cache_invalidate_pattern", pattern=pattern)
        # For pattern-based invalidation, we'd need to iterate
        # For now, just log the pattern
        if isinstance(self._backend, InMemoryCache):
            logger.warning("pattern_invalidation_not_supported_in_memory")

    def cached(
        self,
        key_prefix: str,
        ttl: int | None = None,
        unless: Callable[..., bool] | None = None,
    ):
        """
        Decorator for caching function results.

        Usage:
            @cache_service.cached("exercise", ttl=300)
            async def get_exercise(exercise_id: str):
                ...
        """

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                # Build cache key
                key_parts = [key_prefix]
                # Add positional args (skip self if present)
                for arg in args:
                    if not isinstance(arg, type):  # Skip type objects
                        key_parts.append(str(arg))
                # Add kwargs in sorted order
                for k in sorted(kwargs.keys()):
                    key_parts.append(f"{k}={kwargs[k]}")
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

                # Check unless condition
                if unless and unless(*args, **kwargs):
                    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

                # Try to get from cache
                cached = await self._backend.get(cache_key)
                if cached is not None:
                    logger.debug("cache_hit", function=func.__name__, key=cache_key)
                    return cached

                # Compute value
                value = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

                # Cache it
                await self._backend.set(cache_key, value, ttl or self._ttl)
                logger.debug("cache_set", function=func.__name__, key=cache_key)

                return value

            return wrapper

        return decorator


# Create cache instance
_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    """Get or create cache service instance."""
    global _cache_service
    if _cache_service is None:
        _redis_url = settings.redis_url
        _is_memory = not _redis_url or _redis_url == "redis://localhost:6379/0" or _redis_url.startswith("memory://")
        if not _is_memory:
            backend = RedisCache(_redis_url)
            logger.info("cache_using_redis", url=_redis_url)
        else:
            backend = InMemoryCache()
            logger.info("cache_using_memory")
        _cache_service = CacheService(backend)
    return _cache_service


# Convenience functions
cache = get_cache_service()


async def cached_get(key: str) -> Any | None:
    """Get value from cache."""
    return await cache.get(key)


async def cached_set(key: str, value: Any, ttl: int | None = None) -> None:
    """Set value in cache."""
    await cache.set(key, value, ttl)


async def cached_delete(key: str) -> None:
    """Delete value from cache."""
    await cache.delete(key)

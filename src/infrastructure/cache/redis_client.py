"""
Redis client adapter for JWT blacklist and rate limiting.

Uses the redis.asyncio client for non-blocking operations.
Gracefully degrades if Redis is unavailable (logs warning, doesn't crash).
"""

from __future__ import annotations

import logging

import redis.asyncio as aioredis

from src.infrastructure.config import settings

logger = logging.getLogger("SaveLinks.redis")

# Global Redis connection (initialized lazily)
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create the Redis connection."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection on shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


# ── JWT Blacklist ──────────────────────────────────────────────────


async def blacklist_token(token: str, expire_seconds: int) -> None:
    """Add a JWT token to the blacklist with a TTL matching the token's remaining lifetime."""
    try:
        r = await get_redis()
        await r.setex(f"bl:{token}", expire_seconds, "1")
    except Exception as e:
        logger.warning(f"Failed to blacklist token in Redis: {e}")


async def is_token_blacklisted(token: str) -> bool:
    """Check if a JWT token has been blacklisted (logout)."""
    try:
        r = await get_redis()
        return await r.exists(f"bl:{token}") > 0
    except Exception as e:
        logger.warning(f"Failed to check token blacklist in Redis: {e}")
        return False  # Fail open — if Redis is down, don't block users


# ── Rate Limiting (Sliding Window) ─────────────────────────────────


async def check_rate_limit(
    user_id: str,
    max_requests: int | None = None,
    window_seconds: int | None = None,
) -> tuple[bool, int]:
    """
    Check if a user has exceeded their rate limit.

    Returns:
        (is_allowed, remaining_requests)
    """
    max_req = max_requests or settings.rate_limit_requests
    window = window_seconds or settings.rate_limit_window_seconds

    try:
        r = await get_redis()
        key = f"rl:{user_id}"
        current = await r.incr(key)
        if current == 1:
            await r.expire(key, window)
        remaining = max(0, max_req - current)
        return (current <= max_req, remaining)
    except Exception as e:
        logger.warning(f"Rate limit check failed for {user_id}: {e}")
        return (True, max_req)  # Fail open

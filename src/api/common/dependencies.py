"""
FastAPI dependencies for dependency injection.

Provides database sessions, authenticated user context, and rate limiting.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.link.domain.exceptions import AuthenticationError, RateLimitExceededError
from src.core.link.service.auth_usecases import TokenService
from src.infrastructure.cache.redis_client import check_rate_limit, is_token_blacklisted
from src.infrastructure.config import settings
from src.infrastructure.database.database import async_session_factory


async def get_db() -> AsyncSession:
    """Provide a database session per request with auto commit/rollback."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Reusable dependency type
DBSession = Annotated[AsyncSession, Depends(get_db)]


# Token service singleton
_token_service = TokenService(
    secret_key=settings.secret_key,
    algorithm=settings.jwt_algorithm,
)


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> uuid.UUID:
    """
    Extract and validate JWT from the Authorization header.
    Returns the authenticated user's UUID.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # strip "Bearer "

    # Check blacklist
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = _token_service.verify_token(token)
        return uuid.UUID(payload["sub"])
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Reusable dependency type
CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


async def rate_limit_check(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Rate limiting dependency — checks Redis counter for the user."""
    if not authorization or not authorization.startswith("Bearer "):
        return  # Auth middleware will reject anyway

    token = authorization[7:]
    try:
        payload = _token_service.verify_token(token)
        user_id = payload["sub"]
    except AuthenticationError:
        return  # Auth middleware will reject

    allowed, remaining = await check_rate_limit(user_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {settings.rate_limit_window_seconds} seconds.",
            headers={"Retry-After": str(settings.rate_limit_window_seconds)},
        )

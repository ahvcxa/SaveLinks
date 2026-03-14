"""
Authentication API endpoints.

POST /api/v1/auth/register — Create a new user account
POST /api/v1/auth/login    — Authenticate and receive a JWT token
POST /api/v1/auth/logout   — Blacklist the current token
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, status
from typing import Annotated

from src.api.common.dependencies import DBSession, CurrentUserId, rate_limit_check
from src.api.v1.schemas import (
    MessageResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from src.core.link.service.auth_usecases import (
    LoginUserUseCase,
    RegisterUserUseCase,
    TokenService,
)
from src.infrastructure.cache.redis_client import blacklist_token
from src.infrastructure.config import settings
from src.infrastructure.database.postgres_repository import PostgresUserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(body: UserRegister, db: DBSession):
    user_repo = PostgresUserRepository(db)
    use_case = RegisterUserUseCase(user_repo)
    user = await use_case.execute(body.username, body.password)
    return UserResponse(id=user.id, username=user.username, created_at=user.created_at)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT access token",
)
async def login(body: UserLogin, db: DBSession):
    user_repo = PostgresUserRepository(db)
    use_case = LoginUserUseCase(
        user_repo,
        secret_key=settings.secret_key,
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.access_token_expire_minutes,
    )
    result = await use_case.execute(body.username, body.password)
    return TokenResponse(**result)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout (blacklist the current token)",
    dependencies=[Depends(rate_limit_check)],
)
async def logout(
    current_user_id: CurrentUserId,
    authorization: Annotated[str | None, Header()] = None,
):
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        # Blacklist for the remaining token lifetime (worst case: full expire window)
        await blacklist_token(token, settings.access_token_expire_minutes * 60)
    return MessageResponse(message="Successfully logged out.")

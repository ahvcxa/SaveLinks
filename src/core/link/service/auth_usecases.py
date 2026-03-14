"""
Authentication use cases (business logic).

Handles user registration, login, and JWT token lifecycle.
Uses passlib for password hashing and python-jose for JWT.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.link.domain.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.core.link.domain.models import User
from src.core.link.domain.ports import UserRepositoryPort


# Password hashing context — bcrypt is the default scheme
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterUserUseCase:
    """Registers a new user with a hashed password."""

    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    async def execute(self, username: str, password: str) -> User:
        if not username or not username.strip():
            raise AuthenticationError("Username cannot be empty.")
        if len(password) < 6:
            raise AuthenticationError("Password must be at least 6 characters.")

        # Check if username is taken
        existing = await self._user_repo.get_user_by_username(username.strip())
        if existing is not None:
            raise UserAlreadyExistsError(f"Username '{username}' is already taken.")

        hashed = _pwd_context.hash(password)
        user = User(username=username.strip(), hashed_password=hashed)
        return await self._user_repo.create_user(user)


class LoginUserUseCase:
    """Authenticates a user and returns a JWT access token."""

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        secret_key: str,
        algorithm: str = "HS256",
        expire_minutes: int = 30,
    ) -> None:
        self._user_repo = user_repo
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    async def execute(self, username: str, password: str) -> dict:
        """Returns {"access_token": ..., "token_type": "bearer", "user_id": ...}."""
        if not username or not password:
            raise AuthenticationError("Username and password are required.")

        user = await self._user_repo.get_user_by_username(username.strip())
        if user is None:
            raise AuthenticationError("Invalid username or password.")

        if not _pwd_context.verify(password, user.hashed_password):
            raise AuthenticationError("Invalid username or password.")

        # Create JWT
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._expire_minutes)
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "exp": expire,
        }
        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": str(user.id),
        }


class TokenService:
    """Verifies JWT tokens and extracts user information."""

    def __init__(self, secret_key: str, algorithm: str = "HS256") -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm

    def verify_token(self, token: str) -> dict:
        """
        Decodes and validates a JWT token.
        Returns the payload dict with 'sub' (user_id) and 'username'.
        Raises AuthenticationError if invalid or expired.
        """
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            user_id: str | None = payload.get("sub")
            if user_id is None:
                raise AuthenticationError("Invalid token: missing subject.")
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid or expired token: {e}") from e

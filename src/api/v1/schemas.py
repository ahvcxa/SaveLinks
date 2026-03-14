"""
Pydantic request/response schemas for the API layer.

These are transport-layer concerns — they define what the API accepts and returns.
Separate from domain models to allow independent evolution.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Auth Schemas ───────────────────────────────────────────────────


class UserRegister(BaseModel):
    """Request body for user registration."""
    username: str = Field(..., min_length=3, max_length=50, examples=["johndoe"])
    password: str = Field(..., min_length=6, max_length=128, examples=["s3cureP@ss"])


class UserLogin(BaseModel):
    """Request body for user login."""
    username: str = Field(..., examples=["johndoe"])
    password: str = Field(..., examples=["s3cureP@ss"])


class TokenResponse(BaseModel):
    """Response after successful login."""
    access_token: str
    token_type: str = "bearer"
    user_id: str


class UserResponse(BaseModel):
    """Public user information returned after registration."""
    id: uuid.UUID
    username: str
    created_at: datetime


# ── Link Schemas ───────────────────────────────────────────────────


class LinkCreate(BaseModel):
    """Request body for creating a new link."""
    url: str = Field(..., examples=["https://github.com/python/cpython"])
    title: str | None = Field(None, max_length=500, examples=["CPython GitHub"])
    tags: list[str] = Field(default_factory=list, examples=[["python", "github"]])


class LinkResponse(BaseModel):
    """Single link in API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    url: str
    title: str | None
    description: str | None
    metadata: dict[str, Any]
    is_processed: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class LinkListResponse(BaseModel):
    """Paginated list of links."""
    items: list[LinkResponse]
    total: int
    offset: int
    limit: int


# ── Common Schemas ─────────────────────────────────────────────────


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: str | None = None

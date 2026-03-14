"""
Domain models for SaveLinks.

Pure Python + Pydantic v2 data classes.
This module MUST NOT import anything from infrastructure (SQLAlchemy, FastAPI, etc.).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(BaseModel):
    """Domain entity representing a platform user."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    username: str
    hashed_password: str
    created_at: datetime = Field(default_factory=_utcnow)


class Tag(BaseModel):
    """Domain entity representing a link tag."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    user_id: uuid.UUID


class Link(BaseModel):
    """
    Domain entity representing a saved link.

    The `metadata` field uses a free-form dict (maps to JSONB in PostgreSQL)
    to accommodate varying OpenGraph / Twitter Card / generic meta tags.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    url: str
    title: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_processed: bool = False
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

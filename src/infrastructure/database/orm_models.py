"""
SQLAlchemy ORM models for PostgreSQL (production) and SQLite (testing).

These are infrastructure concerns — they map domain entities to database tables.
The domain layer never imports from here; mapping happens in the repository adapter.

Uses `JSON.with_variant(JSONB, "postgresql")` so the same models work with both
PostgreSQL (JSONB) and SQLite (JSON) backends. GIN indexes are PostgreSQL-only
and are skipped during SQLite table creation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Table,
    Text,
    text,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Cross-backend compatible JSON column: JSONB on PostgreSQL, JSON on others
CompatibleJSON = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# M:N association table for links ↔ tags
link_tags = Table(
    "link_tags",
    Base.metadata,
    Column("link_id", ForeignKey("links.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class UserModel(Base):
    """ORM model for the users table."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    links: Mapped[list["LinkModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    tags: Mapped[list["TagModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )


class LinkModel(Base):
    """
    ORM model for the links table.

    Uses JSONB (PostgreSQL) / JSON (SQLite) for flexible metadata storage
    (OpenGraph, Twitter Cards, etc.) and UUID primary keys for scalability.
    """

    __tablename__ = "links"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", CompatibleJSON, default=dict, nullable=False
    )
    is_processed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["UserModel"] = relationship(back_populates="links")
    tags: Mapped[list["TagModel"]] = relationship(
        secondary=link_tags, back_populates="links", lazy="selectin"
    )

    __table_args__ = (
        # Unique constraint: one URL per user
        Index("ix_links_user_url", "user_id", "url", unique=True),
        # B-Tree index on user_id for fast user-scoped queries
        Index("ix_links_user_id", "user_id"),
    )


# PostgreSQL-only GIN trigram index — created via DDL event listener
# This is skipped entirely on non-PostgreSQL backends (e.g., SQLite in tests)
_GIN_INDEX_SQL = text(
    "CREATE INDEX IF NOT EXISTS ix_links_title_gin "
    "ON links USING gin (title gin_trgm_ops)"
)


@event.listens_for(LinkModel.__table__, "after_create")
def _create_gin_index(target, connection, **kw):
    """Create GIN trigram index only on PostgreSQL."""
    if connection.dialect.name == "postgresql":
        connection.execute(_GIN_INDEX_SQL)


class TagModel(Base):
    """ORM model for the tags table."""

    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    user: Mapped["UserModel"] = relationship(back_populates="tags")
    links: Mapped[list["LinkModel"]] = relationship(
        secondary=link_tags, back_populates="tags", lazy="selectin"
    )

    __table_args__ = (
        # Unique tag name per user
        Index("ix_tags_user_name", "user_id", "name", unique=True),
    )

"""
PostgreSQL repository adapter implementing the domain ports.

This is the concrete implementation that bridges domain logic to PostgreSQL
via async SQLAlchemy. The domain layer never imports this directly.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.link.domain.exceptions import (
    LinkAlreadyExistsError,
    UserAlreadyExistsError,
)
from src.core.link.domain.models import Link, User
from src.core.link.domain.ports import LinkRepositoryPort, UserRepositoryPort
from src.infrastructure.database.orm_models import LinkModel, UserModel


class PostgresLinkRepository(LinkRepositoryPort):
    """Concrete PostgreSQL adapter for link persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Mapping helpers ─────────────────────────────────────────────

    @staticmethod
    def _to_domain(row: LinkModel) -> Link:
        """Convert ORM model → domain entity."""
        return Link(
            id=row.id,
            user_id=row.user_id,
            url=row.url,
            title=row.title,
            description=row.description,
            metadata=row.metadata_json or {},
            is_processed=row.is_processed,
            tags=[t.name for t in row.tags] if row.tags else [],
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ── Port implementations ────────────────────────────────────────

    async def save_link(self, link: Link) -> Link:
        db_link = LinkModel(
            id=link.id,
            user_id=link.user_id,
            url=link.url,
            title=link.title,
            description=link.description,
            metadata_json=link.metadata,
            is_processed=link.is_processed,
        )
        self._session.add(db_link)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            raise LinkAlreadyExistsError(f"URL already saved: {link.url}")
        await self._session.refresh(db_link)
        return self._to_domain(db_link)

    async def get_link(self, link_id: uuid.UUID, user_id: uuid.UUID) -> Link | None:
        stmt = select(LinkModel).where(
            LinkModel.id == link_id,
            LinkModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_links_by_user(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Link]:
        stmt = (
            select(LinkModel)
            .where(LinkModel.user_id == user_id)
            .order_by(LinkModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def search_links(
        self,
        user_id: uuid.UUID,
        query: str,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Link]:
        pattern = f"%{query}%"
        stmt = (
            select(LinkModel)
            .where(
                LinkModel.user_id == user_id,
                or_(
                    LinkModel.title.ilike(pattern),
                    LinkModel.url.ilike(pattern),
                ),
            )
            .order_by(LinkModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def delete_link(self, link_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = (
            delete(LinkModel)
            .where(LinkModel.id == link_id, LinkModel.user_id == user_id)
            .returning(LinkModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update_link_metadata(
        self,
        link_id: uuid.UUID,
        title: str | None,
        description: str | None,
        metadata: dict,
    ) -> None:
        stmt = select(LinkModel).where(LinkModel.id == link_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            row.title = title or row.title
            row.description = description or row.description
            row.metadata_json = metadata
            row.is_processed = True
            await self._session.flush()


class PostgresUserRepository(UserRepositoryPort):
    """Concrete PostgreSQL adapter for user persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(row: UserModel) -> User:
        return User(
            id=row.id,
            username=row.username,
            hashed_password=row.hashed_password,
            created_at=row.created_at,
        )

    async def create_user(self, user: User) -> User:
        db_user = UserModel(
            id=user.id,
            username=user.username,
            hashed_password=user.hashed_password,
        )
        self._session.add(db_user)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            raise UserAlreadyExistsError(f"Username '{user.username}' is already taken.")
        await self._session.refresh(db_user)
        return self._to_domain(db_user)

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

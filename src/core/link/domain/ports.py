"""
Repository ports (interfaces) for SaveLinks.

These ABCs define the contract between domain logic and infrastructure.
Domain services depend only on these ports, never on concrete implementations.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from src.core.link.domain.models import Link, User


class LinkRepositoryPort(ABC):
    """Abstract interface for link persistence operations."""

    @abstractmethod
    async def save_link(self, link: Link) -> Link:
        """Persist a new link. Raises LinkAlreadyExistsError if duplicate URL for user."""
        ...

    @abstractmethod
    async def get_link(self, link_id: uuid.UUID, user_id: uuid.UUID) -> Link | None:
        """Retrieve a single link by ID, scoped to a user."""
        ...

    @abstractmethod
    async def get_links_by_user(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Link]:
        """Retrieve paginated links for a user, ordered by created_at desc."""
        ...

    @abstractmethod
    async def search_links(
        self,
        user_id: uuid.UUID,
        query: str,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Link]:
        """Search links by title/url using ILIKE. Returns paginated results."""
        ...

    @abstractmethod
    async def delete_link(self, link_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a link. Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    async def update_link_metadata(
        self,
        link_id: uuid.UUID,
        title: str | None,
        description: str | None,
        metadata: dict,
    ) -> None:
        """Update scraped metadata and mark link as processed."""
        ...


class UserRepositoryPort(ABC):
    """Abstract interface for user persistence operations."""

    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Persist a new user. Raises UserAlreadyExistsError if username taken."""
        ...

    @abstractmethod
    async def get_user_by_username(self, username: str) -> User | None:
        """Retrieve a user by username."""
        ...

    @abstractmethod
    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve a user by ID."""
        ...

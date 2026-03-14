"""
Link-related use cases (business logic).

These classes orchestrate domain logic and delegate persistence to repository ports.
They MUST NOT import infrastructure code (SQLAlchemy, FastAPI, Redis, etc.).
"""

from __future__ import annotations

import uuid
from urllib.parse import urlparse

from src.core.link.domain.exceptions import (
    InvalidURLError,
    LinkAlreadyExistsError,
    LinkNotFoundError,
)
from src.core.link.domain.models import Link
from src.core.link.domain.ports import LinkRepositoryPort


def _validate_url(url: str) -> str:
    """Basic URL validation. Returns normalized URL or raises InvalidURLError."""
    try:
        result = urlparse(url)
        if result.scheme not in ("http", "https"):
            raise InvalidURLError(f"URL must use http or https scheme, got: {result.scheme!r}")
        if not result.netloc:
            raise InvalidURLError("URL must have a valid domain.")
        return url.strip()
    except InvalidURLError:
        raise
    except Exception as e:
        raise InvalidURLError(f"Invalid URL format: {e}") from e


class SaveLinkUseCase:
    """Validates and persists a new link for a user."""

    def __init__(self, link_repo: LinkRepositoryPort) -> None:
        self._link_repo = link_repo

    async def execute(
        self,
        user_id: uuid.UUID,
        url: str,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> Link:
        validated_url = _validate_url(url)

        link = Link(
            user_id=user_id,
            url=validated_url,
            title=title,
            tags=tags or [],
        )

        return await self._link_repo.save_link(link)


class ListLinksUseCase:
    """Returns paginated links for a user."""

    def __init__(self, link_repo: LinkRepositoryPort) -> None:
        self._link_repo = link_repo

    async def execute(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Link]:
        limit = min(limit, 100)  # Hard cap to prevent abuse
        return await self._link_repo.get_links_by_user(user_id, offset=offset, limit=limit)


class SearchLinksUseCase:
    """Searches links by title/url using server-side query."""

    def __init__(self, link_repo: LinkRepositoryPort) -> None:
        self._link_repo = link_repo

    async def execute(
        self,
        user_id: uuid.UUID,
        query: str,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Link]:
        if not query or not query.strip():
            return []
        limit = min(limit, 100)
        return await self._link_repo.search_links(
            user_id, query.strip(), offset=offset, limit=limit
        )


class GetLinkUseCase:
    """Retrieves a single link by ID."""

    def __init__(self, link_repo: LinkRepositoryPort) -> None:
        self._link_repo = link_repo

    async def execute(self, link_id: uuid.UUID, user_id: uuid.UUID) -> Link:
        link = await self._link_repo.get_link(link_id, user_id)
        if link is None:
            raise LinkNotFoundError(f"Link {link_id} not found.")
        return link


class DeleteLinkUseCase:
    """Deletes a link by ID, scoped to the owning user."""

    def __init__(self, link_repo: LinkRepositoryPort) -> None:
        self._link_repo = link_repo

    async def execute(self, link_id: uuid.UUID, user_id: uuid.UUID) -> None:
        deleted = await self._link_repo.delete_link(link_id, user_id)
        if not deleted:
            raise LinkNotFoundError(f"Link {link_id} not found.")

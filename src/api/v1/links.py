"""
Link CRUD API endpoints.

POST   /api/v1/links          — Save a new link (triggers background metadata scrape)
GET    /api/v1/links          — List user's links (paginated)
GET    /api/v1/links/search   — Search links by title/url
GET    /api/v1/links/{id}     — Get a single link by ID
DELETE /api/v1/links/{id}     — Delete a link
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from src.api.common.dependencies import CurrentUserId, DBSession, rate_limit_check
from src.api.v1.schemas import LinkCreate, LinkListResponse, LinkResponse, MessageResponse
from src.core.link.service.link_usecases import (
    DeleteLinkUseCase,
    GetLinkUseCase,
    ListLinksUseCase,
    SaveLinkUseCase,
    SearchLinksUseCase,
)
from src.infrastructure.database.postgres_repository import PostgresLinkRepository
from src.infrastructure.database.database import async_session_factory
from src.infrastructure.scraper.scraper import extract_metadata

router = APIRouter(prefix="/links", tags=["Links"])


async def _scrape_and_update(link_id: uuid.UUID, url: str) -> None:
    """Background task: scrape metadata from URL and update the link record."""
    metadata = await extract_metadata(url)
    async with async_session_factory() as session:
        try:
            repo = PostgresLinkRepository(session)
            await repo.update_link_metadata(
                link_id=link_id,
                title=metadata.get("title"),
                description=metadata.get("description"),
                metadata=metadata,
            )
            await session.commit()
        except Exception:
            await session.rollback()


@router.post(
    "",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a new link",
    dependencies=[Depends(rate_limit_check)],
)
async def create_link(
    body: LinkCreate,
    db: DBSession,
    current_user_id: CurrentUserId,
    background_tasks: BackgroundTasks,
):
    repo = PostgresLinkRepository(db)
    use_case = SaveLinkUseCase(repo)
    link = await use_case.execute(
        user_id=current_user_id,
        url=body.url,
        title=body.title,
        tags=body.tags,
    )

    # Fire-and-forget metadata scraping
    background_tasks.add_task(_scrape_and_update, link.id, link.url)

    return LinkResponse(
        id=link.id,
        user_id=link.user_id,
        url=link.url,
        title=link.title,
        description=link.description,
        metadata=link.metadata,
        is_processed=link.is_processed,
        tags=link.tags,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.get(
    "",
    response_model=LinkListResponse,
    summary="List all saved links (paginated)",
    dependencies=[Depends(rate_limit_check)],
)
async def list_links(
    db: DBSession,
    current_user_id: CurrentUserId,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    repo = PostgresLinkRepository(db)
    use_case = ListLinksUseCase(repo)
    links = await use_case.execute(current_user_id, offset=offset, limit=limit)
    items = [
        LinkResponse(
            id=l.id,
            user_id=l.user_id,
            url=l.url,
            title=l.title,
            description=l.description,
            metadata=l.metadata,
            is_processed=l.is_processed,
            tags=l.tags,
            created_at=l.created_at,
            updated_at=l.updated_at,
        )
        for l in links
    ]
    return LinkListResponse(items=items, total=len(items), offset=offset, limit=limit)


@router.get(
    "/search",
    response_model=LinkListResponse,
    summary="Search links by title or URL",
    dependencies=[Depends(rate_limit_check)],
)
async def search_links(
    db: DBSession,
    current_user_id: CurrentUserId,
    q: str = Query(..., min_length=1, description="Search query"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    repo = PostgresLinkRepository(db)
    use_case = SearchLinksUseCase(repo)
    links = await use_case.execute(current_user_id, q, offset=offset, limit=limit)
    items = [
        LinkResponse(
            id=l.id,
            user_id=l.user_id,
            url=l.url,
            title=l.title,
            description=l.description,
            metadata=l.metadata,
            is_processed=l.is_processed,
            tags=l.tags,
            created_at=l.created_at,
            updated_at=l.updated_at,
        )
        for l in links
    ]
    return LinkListResponse(items=items, total=len(items), offset=offset, limit=limit)


@router.get(
    "/{link_id}",
    response_model=LinkResponse,
    summary="Get a single link by ID",
    dependencies=[Depends(rate_limit_check)],
)
async def get_link(
    link_id: uuid.UUID,
    db: DBSession,
    current_user_id: CurrentUserId,
):
    repo = PostgresLinkRepository(db)
    use_case = GetLinkUseCase(repo)
    link = await use_case.execute(link_id, current_user_id)
    return LinkResponse(
        id=link.id,
        user_id=link.user_id,
        url=link.url,
        title=link.title,
        description=link.description,
        metadata=link.metadata,
        is_processed=link.is_processed,
        tags=link.tags,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.delete(
    "/{link_id}",
    response_model=MessageResponse,
    summary="Delete a link",
    dependencies=[Depends(rate_limit_check)],
)
async def delete_link(
    link_id: uuid.UUID,
    db: DBSession,
    current_user_id: CurrentUserId,
):
    repo = PostgresLinkRepository(db)
    use_case = DeleteLinkUseCase(repo)
    await use_case.execute(link_id, current_user_id)
    return MessageResponse(message="Link deleted successfully.")

"""
Integration tests for the FastAPI API endpoints.

Uses an in-memory SQLite database (via async SQLAlchemy) to test
the full request/response cycle without requiring PostgreSQL.
"""

from __future__ import annotations

import os
import uuid

# Override settings BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_savelinks.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use DB 15 for tests
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.api.main import create_app
from src.infrastructure.database.orm_models import Base
from src.infrastructure.database import database as db_module


# ── Test Fixtures ──────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="module")
async def app():
    """Create a test app with a fresh in-memory database."""
    # Create test engine
    test_engine = create_async_engine("sqlite+aiosqlite:///test_savelinks.db", echo=False)
    test_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Override the module-level engine and session factory
    db_module.engine = test_engine
    db_module.async_session_factory = test_session_factory

    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    test_app = create_app()
    yield test_app

    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

    # Remove test database file
    if os.path.exists("test_savelinks.db"):
        os.remove("test_savelinks.db")


@pytest_asyncio.fixture(scope="module")
async def client(app):
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ── Auth Tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health endpoint should return 200 with status info."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Registering a new user should return 201 with user info."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "securepass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient):
    """Registering with an existing username should return 409."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "anotherpass"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    """Login with valid credentials should return a JWT token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "securepass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Login with wrong password should return 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401


# ── Helper ─────────────────────────────────────────────────────────

async def _get_token(client: AsyncClient) -> str:
    """Login and return the JWT token for subsequent requests."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "securepass123"},
    )
    return response.json()["access_token"]


# ── Link CRUD Tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_link(client: AsyncClient):
    """Creating a link with valid auth should return 201."""
    token = await _get_token(client)
    response = await client.post(
        "/api/v1/links",
        json={"url": "https://python.org", "title": "Python"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://python.org"
    assert data["title"] == "Python"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_link_unauthorized(client: AsyncClient):
    """Creating a link without auth should return 401."""
    response = await client.post(
        "/api/v1/links",
        json={"url": "https://example.com"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_duplicate_link(client: AsyncClient):
    """Creating the same URL twice should return 409."""
    token = await _get_token(client)
    response = await client.post(
        "/api/v1/links",
        json={"url": "https://python.org"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_links(client: AsyncClient):
    """Listing links should return paginated results."""
    token = await _get_token(client)
    response = await client.get(
        "/api/v1/links",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_search_links(client: AsyncClient):
    """Searching should find links matching the query."""
    token = await _get_token(client)
    response = await client.get(
        "/api/v1/links/search",
        params={"q": "python"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert "python" in data["items"][0]["url"].lower() or "Python" in (data["items"][0]["title"] or "")


@pytest.mark.asyncio
async def test_search_no_results(client: AsyncClient):
    """Search for non-existent links should return empty list."""
    token = await _get_token(client)
    response = await client.get(
        "/api/v1/links/search",
        params={"q": "nonexistentthing12345"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0


@pytest.mark.asyncio
async def test_get_single_link(client: AsyncClient):
    """Getting a link by ID should return the link."""
    token = await _get_token(client)

    # First list to get an ID
    list_resp = await client.get(
        "/api/v1/links",
        headers={"Authorization": f"Bearer {token}"},
    )
    link_id = list_resp.json()["items"][0]["id"]

    response = await client.get(
        f"/api/v1/links/{link_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == link_id


@pytest.mark.asyncio
async def test_get_nonexistent_link(client: AsyncClient):
    """Getting a non-existent link should return 404."""
    token = await _get_token(client)
    fake_id = str(uuid.uuid4())
    response = await client.get(
        f"/api/v1/links/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_link(client: AsyncClient):
    """Deleting a link should return success."""
    token = await _get_token(client)

    # Create a link to delete
    create_resp = await client.post(
        "/api/v1/links",
        json={"url": "https://delete-me.example.com", "title": "Delete Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    link_id = create_resp.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/links/{link_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # Verify it's gone
    get_resp = await client.get(
        f"/api/v1/links/{link_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_url(client: AsyncClient):
    """Saving an invalid URL should return 422."""
    token = await _get_token(client)
    response = await client.post(
        "/api/v1/links",
        json={"url": "not-a-valid-url"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422

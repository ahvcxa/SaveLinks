"""
Async SQLAlchemy engine and session factory for PostgreSQL.

Provides the database connection pool and session lifecycle management.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.infrastructure.config import settings

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=(settings.app_env == "development"),
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# Session factory — each request gets its own session
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncSession:
    """Dependency that provides a database session and handles cleanup."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

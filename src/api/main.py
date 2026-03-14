"""
FastAPI Application Factory.

Creates and configures the FastAPI app with:
- API versioned routes (v1)
- Global error handlers (domain → HTTP mapping)
- Lifespan management (DB + Redis startup/shutdown)
- CORS middleware
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.common.error_handlers import register_error_handlers
from src.api.v1 import auth, links
from src.infrastructure.cache.redis_client import close_redis
from src.infrastructure.config import settings
from src.infrastructure.database.database import engine
from src.infrastructure.database.orm_models import Base

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("SaveLinks")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — setup and teardown."""
    logger.info("Starting SaveLinks API...")

    # Create tables if they don't exist (dev convenience; use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured.")

    yield

    # Cleanup
    logger.info("Shutting down SaveLinks API...")
    await close_redis()
    await engine.dispose()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="SaveLinks API",
        description=(
            "A scalable link saving platform with async API, metadata extraction, "
            "and JWT authentication."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — allow all origins in dev, restrict in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register domain → HTTP error handlers
    register_error_handlers(app)

    # Mount versioned routers
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(links.router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}

    return app


# Application instance for uvicorn
app = create_app()

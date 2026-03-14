"""
Global exception handlers for the FastAPI application.

Maps domain exceptions to proper HTTP status codes.
RULE: Never expose internal errors to the client.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.link.domain.exceptions import (
    AuthenticationError,
    InvalidURLError,
    LinkAlreadyExistsError,
    LinkNotFoundError,
    RateLimitExceededError,
    SaveLinksError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

logger = logging.getLogger("SaveLinks.api")

# Domain exception → (HTTP status code, safe message)
_EXCEPTION_MAP: dict[type[SaveLinksError], int] = {
    LinkAlreadyExistsError: 409,
    LinkNotFoundError: 404,
    InvalidURLError: 422,
    UserNotFoundError: 404,
    UserAlreadyExistsError: 409,
    AuthenticationError: 401,
    RateLimitExceededError: 429,
}


def register_error_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI app instance."""

    @app.exception_handler(SaveLinksError)
    async def domain_exception_handler(
        request: Request, exc: SaveLinksError
    ) -> JSONResponse:
        """Handle all domain exceptions with appropriate HTTP codes."""
        status_code = _EXCEPTION_MAP.get(type(exc), 500)
        if status_code >= 500:
            logger.error(f"Unhandled domain error: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "An internal error occurred."},
            )
        return JSONResponse(
            status_code=status_code,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all for unexpected errors — never leak internals."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Please try again later."},
        )

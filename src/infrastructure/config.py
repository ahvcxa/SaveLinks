"""
Centralized application configuration via environment variables.

Uses Pydantic Settings to load from .env file with validation and defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://savelinks:savelinks@localhost:5432/savelinks"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "change-me-to-a-random-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # Rate Limiting
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60


# Singleton instance
settings = Settings()

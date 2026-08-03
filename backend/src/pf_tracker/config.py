"""Application configuration, sourced from the environment via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository-relative default for the vendored, read-only rules corpus.
_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class Settings(BaseSettings):
    """Runtime settings. Every field is overridable via ``PF_``-prefixed env vars."""

    model_config = SettingsConfigDict(
        env_prefix="PF_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "pf-tracker"
    environment: str = "development"
    debug: bool = False

    # Where the vendored YAML corpus lives (read-only).
    data_dir: Path = Field(default=_DEFAULT_DATA_DIR)

    # Async SQLAlchemy URL; SQLite by default, Postgres-compatible types elsewhere.
    database_url: str = "sqlite+aiosqlite:///./pf_tracker.db"

    # Create tables on startup (dev convenience). Use Alembic migrations in prod.
    auto_create_tables: bool = True

    # CORS origins allowed to call the API (the Vite dev server by default).
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance; used as a FastAPI dependency."""
    return Settings()

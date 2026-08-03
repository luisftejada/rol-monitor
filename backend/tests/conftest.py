"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
import yaml
from httpx import ASGITransport, AsyncClient

from pf_tracker.config import Settings
from pf_tracker.main import create_app
from pf_tracker.rules.repository import RulesRepository


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Settings pointing at the vendored corpus (default data_dir)."""
    return Settings()


@pytest.fixture(scope="session")
def rules_repository(settings: Settings) -> RulesRepository:
    """A repository loaded from the real corpus, shared across the session."""
    return RulesRepository.from_data_dir(settings.data_dir)


@pytest.fixture(scope="session")
def nucleo_raw(settings: Settings) -> dict[str, Any]:
    """The raw ``pathfinder_nucleo.yaml`` document, for data-contract tests."""
    path = Path(settings.data_dir) / "pathfinder_nucleo.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def conjuros_raw(settings: Settings) -> dict[str, Any]:
    """The raw ``pathfinder_conjuros.yaml`` document, for data-contract tests."""
    path = Path(settings.data_dir) / "pathfinder_conjuros.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """An httpx client wired to the ASGI app, with lifespan (corpus load) run."""
    app = create_app()
    # Run FastAPI's lifespan (loads the corpus into app.state); httpx's
    # ASGITransport does not trigger lifespan events on its own.
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

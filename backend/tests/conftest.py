"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from pf_tracker.main import create_app


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """An httpx client wired to the ASGI app in-process (no network)."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

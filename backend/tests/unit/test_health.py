"""Smoke test for the health endpoint."""

from __future__ import annotations

from httpx import AsyncClient

from pf_tracker import __version__


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}

"""Health endpoint: a cheap liveness probe for orchestration and smoke tests."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from pf_tracker import __version__

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Liveness payload."""

    status: Literal["ok"]
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report that the service is up, along with its version."""
    return HealthResponse(status="ok", version=__version__)

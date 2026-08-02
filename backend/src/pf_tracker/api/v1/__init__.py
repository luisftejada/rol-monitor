"""Version 1 of the HTTP API."""

from fastapi import APIRouter

from pf_tracker.api.v1 import health

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)

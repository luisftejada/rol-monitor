"""Version 1 of the HTTP API."""

from fastapi import APIRouter

from pf_tracker.api.v1 import characters, derive, health, rules

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(rules.router)
router.include_router(characters.router)
router.include_router(derive.router)

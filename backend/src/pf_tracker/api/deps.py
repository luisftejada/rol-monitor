"""Shared API dependencies: rules repository access and HTTP caching."""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from pf_tracker.persistence.database import session_scope
from pf_tracker.rules.catalog import catalog_schema_fingerprint
from pf_tracker.rules.repository import RulesRepository
from pf_tracker.services.character_service import CharacterService


class NotModified(Exception):
    """Signals that a cached representation is still fresh (HTTP 304)."""

    def __init__(self, etag: str) -> None:
        self.etag = etag


def get_rules_repository(request: Request) -> RulesRepository:
    """Return the process-wide rules repository loaded during app startup."""
    repo: RulesRepository | None = getattr(request.app.state, "rules_repo", None)
    if repo is None:  # pragma: no cover - defensive; lifespan always sets it
        raise RuntimeError("rules repository is not initialised")
    return repo


# Revalidation is cheap (a 304 carries no body), so the freshness window is kept
# short: a longer one lets clients serve a stale *shape* for that long after the
# API gains a field, which reads as the feature simply not working.
CACHE_CONTROL = "public, max-age=60, must-revalidate"


def rules_cache(
    request: Request,
    response: Response,
    repo: Annotated[RulesRepository, Depends(get_rules_repository)],
) -> None:
    """Attach a versioned ETag and honour ``If-None-Match`` with a 304.

    The validator covers the corpus fingerprint, the catalog DTO shapes, and the
    request URL (path + query). The schema fingerprint matters: adding a field to a
    DTO changes no corpus bytes, so without it clients keep the older response.
    """
    fingerprint = (
        f"{repo.version}:{catalog_schema_fingerprint()}:{request.url.path}?{request.url.query}"
    )
    etag = 'W/"' + hashlib.sha256(fingerprint.encode()).hexdigest()[:16] + '"'
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = CACHE_CONTROL

    if_none_match = request.headers.get("if-none-match")
    if if_none_match and etag in {tag.strip() for tag in if_none_match.split(",")}:
        raise NotModified(etag)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped database session (commit on success, rollback on error)."""
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async for session in session_scope(factory):
        yield session


def get_character_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    rules: Annotated[RulesRepository, Depends(get_rules_repository)],
) -> CharacterService:
    return CharacterService(session, rules)


CharacterServiceDep = Annotated[CharacterService, Depends(get_character_service)]

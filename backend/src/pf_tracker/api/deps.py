"""Shared API dependencies: rules repository access and HTTP caching."""

from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import Depends, Request, Response

from pf_tracker.rules.repository import RulesRepository


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


CACHE_CONTROL = "public, max-age=3600"


def rules_cache(
    request: Request,
    response: Response,
    repo: Annotated[RulesRepository, Depends(get_rules_repository)],
) -> None:
    """Attach a corpus-versioned ETag and honour ``If-None-Match`` with a 304.

    The rules catalog is immutable per process, so the validator is derived from
    the corpus fingerprint plus the request URL (path + query).
    """
    fingerprint = f"{repo.version}:{request.url.path}?{request.url.query}"
    etag = 'W/"' + hashlib.sha256(fingerprint.encode()).hexdigest()[:16] + '"'
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = CACHE_CONTROL

    if_none_match = request.headers.get("if-none-match")
    if if_none_match and etag in {tag.strip() for tag in if_none_match.split(",")}:
        raise NotModified(etag)

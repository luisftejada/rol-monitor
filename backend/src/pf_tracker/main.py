"""Application factory, lifespan, and dependency wiring."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from pf_tracker import __version__
from pf_tracker.api.deps import NotModified
from pf_tracker.api.v1 import router as api_v1_router
from pf_tracker.config import Settings, get_settings
from pf_tracker.rules.repository import RuleNotFoundError, RulesRepository


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load the read-only rules corpus once, at startup."""
    settings: Settings = app.state.settings
    app.state.rules_repo = RulesRepository.from_data_dir(settings.data_dir)
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = settings or get_settings()

    app = FastAPI(
        title="pf-tracker",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = settings

    @app.exception_handler(NotModified)
    async def _not_modified(_request: Request, exc: NotModified) -> Response:
        return Response(
            status_code=304,
            headers={"ETag": exc.etag, "Cache-Control": "public, max-age=3600"},
        )

    @app.exception_handler(RuleNotFoundError)
    async def _rule_not_found(_request: Request, exc: RuleNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router)
    return app


app = create_app()

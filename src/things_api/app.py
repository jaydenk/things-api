"""FastAPI application factory and entrypoint."""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from things_api.auth import require_token
from things_api.config import Settings
from things_api.models import HealthResponse
from things_api.ratelimit import AuthRateLimiter
from things_api.services.reader import ThingsReader
from things_api.services.writer import ThingsWriter

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title="Things API",
        description="REST API for Things 3 — expose your tasks over HTTP",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        dependencies=[require_token(settings.things_api_token.get_secret_value())],
    )

    app.add_middleware(AuthRateLimiter, max_failures=10, window=60)

    reader = ThingsReader(
        db_path=str(settings.things_db_path) if settings.things_db_path else None,
    )
    writer = (
        ThingsWriter(
            auth_token=settings.things_auth_token.get_secret_value(),
            verify_timeout=settings.things_verify_timeout,
        )
        if settings.write_enabled
        else None
    )

    app.state.settings = settings
    app.state.reader = reader
    app.state.writer = writer

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, exc: RuntimeError):
        logger.exception("Unhandled runtime error")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    @app.get("/health", response_model=HealthResponse)
    async def health():
        try:
            reader.inbox()
            db_ok = True
        except Exception:
            db_ok = False

        return HealthResponse(
            status="healthy" if db_ok else "degraded",
            read=db_ok,
            write=settings.write_enabled,
        )

    from things_api.routers import todos, projects, lists, tags, areas, search
    app.include_router(todos.router)
    app.include_router(projects.router)
    app.include_router(lists.router)
    app.include_router(tags.router)
    app.include_router(areas.router)
    app.include_router(search.router)

    return app


def main() -> None:
    """CLI entrypoint."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings()
    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.things_api_host,
        port=settings.things_api_port,
    )

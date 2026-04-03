"""FastAPI application factory and entrypoint."""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from things_api.auth import require_token
from things_api.config import Settings
from things_api.models import HealthResponse
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
        dependencies=[require_token(settings.things_api_token)],
    )

    reader = ThingsReader(
        db_path=str(settings.things_db_path) if settings.things_db_path else None,
    )
    writer = (
        ThingsWriter(
            auth_token=settings.things_auth_token,
            verify_timeout=settings.things_verify_timeout,
        )
        if settings.write_enabled
        else None
    )

    app.state.settings = settings
    app.state.reader = reader
    app.state.writer = writer

    @app.get("/health", response_model=HealthResponse)
    async def health():
        return HealthResponse(
            status="healthy",
            read=True,
            write=settings.write_enabled,
        )

    # Routers registered here as they are built in subsequent tasks

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

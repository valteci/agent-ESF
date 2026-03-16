from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from esf_agent_service.api.router import api_router
from esf_agent_service.application.container import build_service_container
from esf_agent_service.core.config import get_settings
from esf_agent_service.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    container = build_service_container(settings)
    app.state.container = container
    yield
    await container.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="ESF Agent Service",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app

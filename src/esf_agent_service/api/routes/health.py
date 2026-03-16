from __future__ import annotations

from fastapi import APIRouter, Depends

from esf_agent_service.api.dependencies import get_container
from esf_agent_service.application.container import ServiceContainer

router = APIRouter()


@router.get("/health")
async def healthcheck(container: ServiceContainer = Depends(get_container)) -> dict[str, str]:
    settings = container.settings
    return {
        "status": "ok",
        "environment": settings.app_env,
        "transport_mode": settings.telegram_transport_mode,
    }

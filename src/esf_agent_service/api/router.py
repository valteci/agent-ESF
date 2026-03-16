from fastapi import APIRouter

from esf_agent_service.api.routes.health import router as health_router
from esf_agent_service.api.routes.telegram import router as telegram_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(telegram_router, prefix="/telegram", tags=["telegram"])

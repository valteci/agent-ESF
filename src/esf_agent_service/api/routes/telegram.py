from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from esf_agent_service.api.dependencies import get_container
from esf_agent_service.application.container import ServiceContainer

router = APIRouter()


class TelegramWebhookResponse(BaseModel):
    status: str
    detail: str
    storage_path: str | None = None


@router.post("/webhook", response_model=TelegramWebhookResponse)
async def receive_webhook(
    update: dict[str, Any],
    request: Request,
    container: ServiceContainer = Depends(get_container),
) -> TelegramWebhookResponse:
    expected_secret = container.settings.telegram_webhook_secret
    if expected_secret is not None:
        incoming_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if incoming_secret != expected_secret.get_secret_value():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Telegram webhook secret.",
            )

    result = await container.ingestion_service.ingest_update(update)
    return TelegramWebhookResponse(
        status=result.status,
        detail=result.detail,
        storage_path=result.storage_path,
    )

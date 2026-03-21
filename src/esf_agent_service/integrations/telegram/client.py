from __future__ import annotations

from typing import Any

import httpx

from esf_agent_service.core.config import Settings


class TelegramApiError(RuntimeError):
    pass


class TelegramBotClient:
    def __init__(self, *, settings: Settings, http_client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http_client = http_client

    @property
    def _bot_api_base(self) -> str:
        token = self._settings.telegram_bot_token.get_secret_value()
        return f"{self._settings.telegram_base_url}/bot{token}"

    @property
    def _file_api_base(self) -> str:
        token = self._settings.telegram_bot_token.get_secret_value()
        return f"{self._settings.telegram_base_url}/file/bot{token}"

    async def get_updates(self, *, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            payload["offset"] = offset
        result = await self._request_json("POST", "/getUpdates", json=payload)
        return list(result)

    async def get_file(self, file_id: str) -> dict[str, Any]:
        return await self._request_json("POST", "/getFile", json={"file_id": file_id})

    async def download_file(self, telegram_file_path: str) -> bytes:
        response = await self._http_client.get(f"{self._file_api_base}/{telegram_file_path}")
        response.raise_for_status()
        return response.content

    async def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        return await self._request_json("POST", "/sendMessage", json=payload)

    async def send_chat_action(
        self,
        *,
        chat_id: int,
        action: str,
    ) -> bool:
        result = await self._request_json(
            "POST",
            "/sendChatAction",
            json={"chat_id": chat_id, "action": action},
        )
        return bool(result)

    async def set_webhook(
        self,
        *,
        url: str,
        secret_token: str | None = None,
        drop_pending_updates: bool = False,
    ) -> bool:
        payload: dict[str, Any] = {
            "url": url,
            "drop_pending_updates": drop_pending_updates,
        }
        if secret_token:
            payload["secret_token"] = secret_token
        result = await self._request_json("POST", "/setWebhook", json=payload)
        return bool(result)

    async def delete_webhook(self, *, drop_pending_updates: bool = False) -> bool:
        result = await self._request_json(
            "POST",
            "/deleteWebhook",
            json={"drop_pending_updates": drop_pending_updates},
        )
        return bool(result)

    async def _request_json(self, method: str, path: str, *, json: dict[str, Any]) -> Any:
        response = await self._http_client.request(
            method,
            f"{self._bot_api_base}{path}",
            json=json,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            description = payload.get("description", "Telegram API request failed.")
            raise TelegramApiError(description)
        return payload.get("result")

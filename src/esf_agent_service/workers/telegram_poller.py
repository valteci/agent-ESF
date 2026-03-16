from __future__ import annotations

import asyncio
import logging

import httpx

from esf_agent_service.application.container import build_service_container
from esf_agent_service.core.config import get_settings
from esf_agent_service.core.logging import configure_logging
from esf_agent_service.integrations.telegram.client import TelegramApiError

logger = logging.getLogger(__name__)


class TelegramPollingWorker:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._state_file = self._settings.polling_state_root / "offset.txt"
        self._container = build_service_container(self._settings)

    async def run(self) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)

        if self._settings.telegram_transport_mode != "polling":
            raise RuntimeError("TELEGRAM_TRANSPORT_MODE must be 'polling' to run the poller.")

        if self._settings.telegram_clear_webhook_on_polling_start:
            await self._container.telegram_client.delete_webhook(drop_pending_updates=False)

        offset = self._load_offset()

        try:
            while True:
                try:
                    updates = await self._container.telegram_client.get_updates(
                        offset=offset,
                        timeout=self._settings.telegram_polling_timeout_seconds,
                    )
                    for update in updates:
                        result = await self._container.ingestion_service.ingest_update(update)
                        update_id = int(update["update_id"])
                        offset = update_id + 1
                        self._persist_offset(offset)
                        logger.info(
                            "Polling processed update_id=%s status=%s",
                            update_id,
                            result.status,
                        )
                except (httpx.HTTPError, TelegramApiError) as exc:
                    logger.warning("Polling cycle failed: %s", exc)
                await asyncio.sleep(self._settings.telegram_polling_sleep_seconds)
        finally:
            await self._container.aclose()

    def _load_offset(self) -> int | None:
        if not self._state_file.exists():
            return None
        raw_value = self._state_file.read_text(encoding="utf-8").strip()
        if not raw_value:
            return None
        return int(raw_value)

    def _persist_offset(self, offset: int) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state_file.write_text(f"{offset}\n", encoding="utf-8")


def main() -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    worker = TelegramPollingWorker()
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        logger.info("Telegram poller interrupted by user.")
        return 0
    except TelegramApiError as exc:
        logger.error("Telegram API error while polling: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

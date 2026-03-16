from __future__ import annotations

import hashlib
import logging

from esf_agent_service.application.processors import MessageProcessor
from esf_agent_service.core.config import Settings
from esf_agent_service.domain.models import (
    InboundTelegramMessage,
    IngestionResult,
    TelegramAttachmentDownload,
)
from esf_agent_service.integrations.telegram.client import TelegramBotClient
from esf_agent_service.integrations.telegram.parser import TelegramUpdateParser
from esf_agent_service.repositories.filesystem_inbox import FilesystemInboxRepository

logger = logging.getLogger(__name__)


class TelegramIngestionService:
    def __init__(
        self,
        *,
        settings: Settings,
        telegram_client: TelegramBotClient,
        update_parser: TelegramUpdateParser,
        inbox_repository: FilesystemInboxRepository,
        message_processor: MessageProcessor,
    ) -> None:
        self._settings = settings
        self._telegram_client = telegram_client
        self._update_parser = update_parser
        self._inbox_repository = inbox_repository
        self._message_processor = message_processor

    async def ingest_update(self, update: dict) -> IngestionResult:
        message = self._update_parser.parse(update)
        if message is None:
            return IngestionResult(
                status="ignored",
                detail="Unsupported Telegram update type.",
                storage_path=None,
            )

        if not self._is_allowed(message):
            logger.info(
                "Ignoring Telegram message due to allowlist rules: chat_id=%s user_id=%s",
                message.chat_id,
                message.sender_user_id,
            )
            return IngestionResult(
                status="ignored",
                detail="Telegram message ignored by allowlist.",
                storage_path=None,
            )

        downloads = await self._download_attachments(message)
        stored_message = self._inbox_repository.save(
            message=message,
            raw_update=update,
            downloads=downloads,
        )

        if not stored_message.duplicate:
            await self._message_processor.process(stored_message)
            await self._maybe_ack(message)
            return IngestionResult(
                status="stored",
                detail="Telegram message stored successfully.",
                storage_path=stored_message.storage_path,
            )

        return IngestionResult(
            status="duplicate",
            detail="Telegram update was already stored.",
            storage_path=stored_message.storage_path,
        )

    def _is_allowed(self, message: InboundTelegramMessage) -> bool:
        allowed_users = self._settings.telegram_allowed_user_ids
        allowed_chats = self._settings.telegram_allowed_chat_ids

        if allowed_users and message.sender_user_id not in allowed_users:
            return False
        if allowed_chats and message.chat_id not in allowed_chats:
            return False
        return True

    async def _download_attachments(
        self, message: InboundTelegramMessage
    ) -> list[TelegramAttachmentDownload]:
        if not self._settings.telegram_download_media:
            return []

        downloads: list[TelegramAttachmentDownload] = []
        for attachment in message.attachments:
            file_info = await self._telegram_client.get_file(attachment.telegram_file_id)
            telegram_file_path = file_info.get("file_path")
            if not telegram_file_path:
                logger.warning(
                    "Telegram file path missing for attachment %s in update %s",
                    attachment.telegram_file_id,
                    message.update_id,
                )
                continue

            content = await self._telegram_client.download_file(telegram_file_path)
            downloads.append(
                TelegramAttachmentDownload(
                    attachment=attachment,
                    telegram_file_path=telegram_file_path,
                    content=content,
                    sha256=hashlib.sha256(content).hexdigest(),
                )
            )
        return downloads

    async def _maybe_ack(self, message: InboundTelegramMessage) -> None:
        if not self._settings.telegram_ack_enabled:
            return

        await self._telegram_client.send_message(
            chat_id=message.chat_id,
            text=self._settings.telegram_ack_template,
            reply_to_message_id=message.message_id,
        )

from __future__ import annotations

import logging
from typing import Protocol

from esf_agent_service.domain.models import StoredInboundMessage

logger = logging.getLogger(__name__)


class MessageProcessor(Protocol):
    async def process(self, stored_message: StoredInboundMessage) -> None:
        ...


class LoggingMessageProcessor:
    async def process(self, stored_message: StoredInboundMessage) -> None:
        logger.info(
            "Stored Telegram message ready for next pipeline step: chat_id=%s message_id=%s path=%s",
            stored_message.message.chat_id,
            stored_message.message.message_id,
            stored_message.storage_path,
        )

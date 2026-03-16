from __future__ import annotations

from dataclasses import dataclass

import httpx

from esf_agent_service.application.processors import LoggingMessageProcessor
from esf_agent_service.application.services.telegram_ingestion import TelegramIngestionService
from esf_agent_service.core.config import Settings
from esf_agent_service.integrations.telegram.client import TelegramBotClient
from esf_agent_service.integrations.telegram.parser import TelegramUpdateParser
from esf_agent_service.repositories.filesystem_inbox import FilesystemInboxRepository


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    http_client: httpx.AsyncClient
    telegram_client: TelegramBotClient
    inbox_repository: FilesystemInboxRepository
    update_parser: TelegramUpdateParser
    message_processor: LoggingMessageProcessor
    ingestion_service: TelegramIngestionService

    async def aclose(self) -> None:
        await self.http_client.aclose()


def build_service_container(settings: Settings) -> ServiceContainer:
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=60.0)
    )
    telegram_client = TelegramBotClient(settings=settings, http_client=http_client)
    inbox_repository = FilesystemInboxRepository(settings.inbox_root)
    update_parser = TelegramUpdateParser()
    message_processor = LoggingMessageProcessor()
    ingestion_service = TelegramIngestionService(
        settings=settings,
        telegram_client=telegram_client,
        update_parser=update_parser,
        inbox_repository=inbox_repository,
        message_processor=message_processor,
    )
    return ServiceContainer(
        settings=settings,
        http_client=http_client,
        telegram_client=telegram_client,
        inbox_repository=inbox_repository,
        update_parser=update_parser,
        message_processor=message_processor,
        ingestion_service=ingestion_service,
    )

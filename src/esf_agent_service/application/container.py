from __future__ import annotations

from dataclasses import dataclass

import httpx

from esf_agent_service.application.agent_runtime import (
    AgentPromptBuilder,
    BackgroundTaskDispatcher,
    CommandAgentRunner,
    SkippedAgentRunner,
)
from esf_agent_service.application.processors import (
    AgentMessageProcessor,
    LoggingMessageProcessor,
    MessageProcessor,
)
from esf_agent_service.application.services.telegram_ingestion import TelegramIngestionService
from esf_agent_service.core.config import Settings
from esf_agent_service.integrations.telegram.client import TelegramBotClient
from esf_agent_service.integrations.telegram.parser import TelegramUpdateParser
from esf_agent_service.repositories.filesystem_agent_results import (
    FilesystemAgentResultsRepository,
)
from esf_agent_service.repositories.filesystem_inbox import FilesystemInboxRepository


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    http_client: httpx.AsyncClient
    telegram_client: TelegramBotClient
    inbox_repository: FilesystemInboxRepository
    update_parser: TelegramUpdateParser
    task_dispatcher: BackgroundTaskDispatcher
    message_processor: MessageProcessor
    ingestion_service: TelegramIngestionService

    async def aclose(self) -> None:
        await self.task_dispatcher.aclose()
        await self.http_client.aclose()


def build_service_container(settings: Settings) -> ServiceContainer:
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=60.0)
    )
    telegram_client = TelegramBotClient(settings=settings, http_client=http_client)
    inbox_repository = FilesystemInboxRepository(settings.inbox_root)
    update_parser = TelegramUpdateParser()
    task_dispatcher = BackgroundTaskDispatcher()
    message_processor = _build_message_processor(settings, task_dispatcher)
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
        task_dispatcher=task_dispatcher,
        message_processor=message_processor,
        ingestion_service=ingestion_service,
    )


def _build_message_processor(
    settings: Settings,
    task_dispatcher: BackgroundTaskDispatcher,
) -> MessageProcessor:
    if not settings.agent_enabled:
        return LoggingMessageProcessor()

    prompt_builder = AgentPromptBuilder(
        settings.agent_instructions_path,
        settings.agent_skills_search_roots,
    )
    results_repository = FilesystemAgentResultsRepository()
    if settings.agent_command.strip():
        runner = CommandAgentRunner(
            command_template=settings.agent_command,
            workdir=settings.agent_workdir,
            timeout_seconds=settings.agent_timeout_seconds,
        )
    else:
        runner = SkippedAgentRunner(
            "AGENT_COMMAND is not configured. Request persisted without agent execution."
        )

    return AgentMessageProcessor(
        prompt_builder=prompt_builder,
        runner=runner,
        results_repository=results_repository,
        execution_mode=settings.agent_execution_mode,
        dispatcher=task_dispatcher,
    )

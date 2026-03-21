from __future__ import annotations

import logging
from typing import Literal, Protocol

from esf_agent_service.application.agent_runtime import (
    AgentPromptBuilder,
    AgentRunner,
    BackgroundTaskDispatcher,
    utcnow,
    AgentExecutionResult,
)
from esf_agent_service.domain.models import StoredInboundMessage
from esf_agent_service.repositories.filesystem_agent_results import (
    FilesystemAgentResultsRepository,
)

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


class AgentMessageProcessor:
    def __init__(
        self,
        *,
        prompt_builder: AgentPromptBuilder,
        runner: AgentRunner,
        results_repository: FilesystemAgentResultsRepository,
        execution_mode: Literal["background", "inline"],
        dispatcher: BackgroundTaskDispatcher | None = None,
    ) -> None:
        if execution_mode == "background" and dispatcher is None:
            raise ValueError("dispatcher is required when execution_mode='background'")

        self._prompt_builder = prompt_builder
        self._runner = runner
        self._results_repository = results_repository
        self._execution_mode = execution_mode
        self._dispatcher = dispatcher

    async def process(self, stored_message: StoredInboundMessage) -> None:
        request = self._prompt_builder.build(stored_message)
        self._results_repository.save_request(request)

        if self._execution_mode == "background":
            assert self._dispatcher is not None
            self._dispatcher.submit(
                label=(
                    "agent-run:"
                    f"chat-{stored_message.message.chat_id}:"
                    f"message-{stored_message.message.message_id}"
                ),
                coroutine=self._execute_and_store(request),
            )
            logger.info(
                "Queued agent execution for chat_id=%s message_id=%s storage_path=%s",
                stored_message.message.chat_id,
                stored_message.message.message_id,
                stored_message.storage_path,
            )
            return

        await self._execute_and_store(request)

    async def _execute_and_store(self, request) -> None:
        try:
            result = await self._runner.run(request)
        except Exception as exc:
            logger.exception("Agent execution failed for storage_path=%s", request.storage_path)
            timestamp = utcnow()
            result = AgentExecutionResult(
                status="failed",
                detail=str(exc),
                command=[],
                exit_code=None,
                started_at=timestamp,
                finished_at=timestamp,
                stdout="",
                stderr="",
            )

        self._results_repository.save_result(request.storage_path, result)
        logger.info(
            "Agent execution finished with status=%s chat_id=%s message_id=%s storage_path=%s",
            result.status,
            request.chat_id,
            request.message_id,
            request.storage_path,
        )

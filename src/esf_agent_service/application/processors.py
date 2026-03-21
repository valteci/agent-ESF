from __future__ import annotations

import asyncio
import logging
import time
from typing import Literal, Protocol

from esf_agent_service.application.agent_runtime import (
    AgentPromptBuilder,
    AgentRunner,
    BackgroundTaskDispatcher,
    utcnow,
    AgentExecutionResult,
)
from esf_agent_service.domain.models import StoredInboundMessage
from esf_agent_service.integrations.telegram.client import TelegramBotClient
from esf_agent_service.repositories.filesystem_agent_results import (
    FilesystemAgentResultsRepository,
)

logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 4000
TYPING_ACTION = "typing"
TYPING_INTERVAL_SECONDS = 4.0
MIN_TYPING_SECONDS = 1.5


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
        telegram_client: TelegramBotClient | None = None,
        telegram_feedback_enabled: bool = True,
        dispatcher: BackgroundTaskDispatcher | None = None,
    ) -> None:
        if execution_mode == "background" and dispatcher is None:
            raise ValueError("dispatcher is required when execution_mode='background'")

        self._prompt_builder = prompt_builder
        self._runner = runner
        self._results_repository = results_repository
        self._execution_mode = execution_mode
        self._telegram_client = telegram_client
        self._telegram_feedback_enabled = telegram_feedback_enabled
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
        typing_task: asyncio.Task[None] | None = None
        typing_started_at: float | None = None
        if self._should_send_telegram_feedback():
            typing_started_at = await self._start_typing_feedback(
                chat_id=request.chat_id,
                message_id=request.message_id,
            )
            if typing_started_at is not None:
                typing_task = asyncio.create_task(
                    self._send_typing_heartbeat(
                        chat_id=request.chat_id,
                        message_id=request.message_id,
                    )
                )
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
        finally:
            if typing_task is not None:
                typing_task.cancel()
                try:
                    await typing_task
                except asyncio.CancelledError:
                    pass
            if typing_started_at is not None:
                elapsed = time.monotonic() - typing_started_at
                remaining = MIN_TYPING_SECONDS - elapsed
                if remaining > 0:
                    await asyncio.sleep(remaining)

        self._results_repository.save_result(request.storage_path, result)
        await self._maybe_send_telegram_result(request, result)
        logger.info(
            "Agent execution finished with status=%s chat_id=%s message_id=%s storage_path=%s",
            result.status,
            request.chat_id,
            request.message_id,
            request.storage_path,
        )

    def _should_send_telegram_feedback(self) -> bool:
        return self._telegram_client is not None and self._telegram_feedback_enabled

    async def _start_typing_feedback(self, *, chat_id: int, message_id: int) -> float | None:
        assert self._telegram_client is not None
        try:
            await self._telegram_client.send_chat_action(
                chat_id=chat_id,
                action=TYPING_ACTION,
            )
        except Exception:
            logger.exception(
                "Failed to send initial Telegram typing feedback: chat_id=%s message_id=%s",
                chat_id,
                message_id,
            )
            return None
        return time.monotonic()

    async def _send_typing_heartbeat(self, *, chat_id: int, message_id: int) -> None:
        assert self._telegram_client is not None
        while True:
            await asyncio.sleep(TYPING_INTERVAL_SECONDS)
            try:
                await self._telegram_client.send_chat_action(
                    chat_id=chat_id,
                    action=TYPING_ACTION,
                )
            except Exception:
                logger.exception(
                    "Failed to send Telegram typing heartbeat: chat_id=%s message_id=%s",
                    chat_id,
                    message_id,
                )
                return

    async def _maybe_send_telegram_result(self, request, result: AgentExecutionResult) -> None:
        if not self._should_send_telegram_feedback():
            return

        response_text = self._response_text_for_result(result)
        if not response_text:
            return

        assert self._telegram_client is not None
        try:
            for chunk in self._chunk_telegram_message(response_text):
                await self._telegram_client.send_message(
                    chat_id=request.chat_id,
                    text=chunk,
                    reply_to_message_id=request.message_id,
                )
        except Exception:
            logger.exception(
                "Failed to send Telegram agent response: chat_id=%s message_id=%s storage_path=%s",
                request.chat_id,
                request.message_id,
                request.storage_path,
            )

    def _response_text_for_result(self, result: AgentExecutionResult) -> str:
        for candidate in (result.stdout, result.stderr, result.detail):
            normalized = candidate.strip()
            if normalized:
                return normalized
        return ""

    def _chunk_telegram_message(self, text: str) -> list[str]:
        stripped = text.strip()
        if not stripped:
            return []

        chunks: list[str] = []
        remaining = stripped
        while len(remaining) > TELEGRAM_MESSAGE_LIMIT:
            split_at = remaining.rfind("\n", 0, TELEGRAM_MESSAGE_LIMIT + 1)
            if split_at <= 0:
                split_at = TELEGRAM_MESSAGE_LIMIT
            chunk = remaining[:split_at].strip()
            if chunk:
                chunks.append(chunk)
            remaining = remaining[split_at:].lstrip("\n")
        if remaining:
            chunks.append(remaining)
        return chunks

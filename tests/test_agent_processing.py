from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from esf_agent_service.application.agent_runtime import (
    AgentExecutionRequest,
    AgentExecutionResult,
    AgentPromptBuilder,
    AgentSkillReference,
    BackgroundTaskDispatcher,
    CommandAgentRunner,
)
from esf_agent_service.application.processors import AgentMessageProcessor
from esf_agent_service.domain.models import (
    InboundTelegramMessage,
    StoredInboundMessage,
    TelegramAttachment,
    TelegramAttachmentDownload,
)
from esf_agent_service.repositories.filesystem_agent_results import (
    FilesystemAgentResultsRepository,
)
from esf_agent_service.repositories.filesystem_inbox import FilesystemInboxRepository


def test_command_agent_runner_passes_prompt_to_subprocess(tmp_path) -> None:
    request = AgentExecutionRequest(
        chat_id=1,
        message_id=2,
        update_id=3,
        sent_at=datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        normalized_text="compra mercado",
        project_root=str(tmp_path),
        storage_path=str(tmp_path),
        message_path=str(tmp_path / "message.json"),
        raw_update_path=str(tmp_path / "raw_update.json"),
        attachments_dir=str(tmp_path / "attachments"),
        attachments=[],
        instructions_path=str(tmp_path / "AGENTS.md"),
        skills=[],
        prompt="saida do prompt\n",
    )
    runner = CommandAgentRunner(
        command_template="bash -lc 'cat'",
        workdir=tmp_path,
        timeout_seconds=5,
    )

    result = asyncio.run(runner.run(request))

    assert result.status == "completed"
    assert result.exit_code == 0
    assert result.stdout == "saida do prompt\n"
    assert result.stderr == ""


def test_agent_message_processor_persists_request_and_inline_result(tmp_path) -> None:
    instructions_path = _write_instructions_and_skill(tmp_path)
    stored_message = _build_stored_message(tmp_path)
    processor = AgentMessageProcessor(
        prompt_builder=AgentPromptBuilder(instructions_path),
        runner=_StaticRunner(stdout='{"transactions": []}\n'),
        results_repository=FilesystemAgentResultsRepository(),
        execution_mode="inline",
    )

    asyncio.run(processor.process(stored_message))

    agent_dir = Path(stored_message.storage_path) / "agent"
    request_payload = json.loads((agent_dir / "request.json").read_text(encoding="utf-8"))
    result_payload = json.loads((agent_dir / "result.json").read_text(encoding="utf-8"))

    assert (agent_dir / "prompt.txt").is_file()
    assert (agent_dir / "stdout.txt").read_text(encoding="utf-8") == '{"transactions": []}\n'
    assert request_payload["normalized_text"] == "compra mercado\n\nnota do cartao"
    assert request_payload["project_root"] == str(tmp_path)
    assert request_payload["instructions_path"] == str(instructions_path)
    assert request_payload["attachments"][0]["local_path"].endswith("nota.pdf")
    assert request_payload["skills"] == [
        {
            "description": "Skill de teste para o agente.",
            "name": "fake-skill",
            "path": str(tmp_path / ".agents" / "skills" / "fake-skill" / "SKILL.md"),
            "relative_path": ".agents/skills/fake-skill/SKILL.md",
        }
    ]
    assert result_payload["status"] == "completed"
    assert result_payload["stdout_path"].endswith("stdout.txt")
    assert "Leia primeiro o arquivo AGENTS.md" in request_payload["prompt"]
    assert "Use o schema do projeto." not in request_payload["prompt"]
    assert "fake-skill: Skill de teste para o agente." in request_payload["prompt"]


def test_agent_message_processor_background_mode_does_not_block(tmp_path) -> None:
    instructions_path = _write_instructions_and_skill(tmp_path)
    stored_message = _build_stored_message(tmp_path)
    runner = _BlockingRunner()
    dispatcher = BackgroundTaskDispatcher()
    processor = AgentMessageProcessor(
        prompt_builder=AgentPromptBuilder(instructions_path),
        runner=runner,
        results_repository=FilesystemAgentResultsRepository(),
        execution_mode="background",
        dispatcher=dispatcher,
    )

    async def scenario() -> None:
        await processor.process(stored_message)
        agent_dir = Path(stored_message.storage_path) / "agent"
        assert (agent_dir / "request.json").is_file()
        assert not (agent_dir / "result.json").exists()

        await runner.started.wait()
        runner.release.set()
        await dispatcher.aclose()

        assert (agent_dir / "result.json").is_file()

    asyncio.run(scenario())


class _StaticRunner:
    def __init__(self, *, stdout: str) -> None:
        self._stdout = stdout

    async def run(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        timestamp = datetime.now(timezone.utc)
        return AgentExecutionResult(
            status="completed",
            detail="ok",
            command=["fake-agent"],
            exit_code=0,
            started_at=timestamp,
            finished_at=timestamp,
            stdout=self._stdout,
            stderr="",
        )


class _BlockingRunner:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def run(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        self.started.set()
        await self.release.wait()
        timestamp = datetime.now(timezone.utc)
        return AgentExecutionResult(
            status="completed",
            detail="ok",
            command=["fake-agent"],
            exit_code=0,
            started_at=timestamp,
            finished_at=timestamp,
            stdout='{"transactions": []}\n',
            stderr="",
        )


def _build_stored_message(tmp_path: Path) -> StoredInboundMessage:
    repository = FilesystemInboxRepository(tmp_path / "inbox")
    message = InboundTelegramMessage(
        update_id=10,
        update_type="message",
        message_id=20,
        chat_id=30,
        chat_type="private",
        sender_user_id=40,
        sender_username="tester",
        sender_first_name="Test",
        sent_at=datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        text="compra mercado",
        caption="nota do cartao",
        media_group_id=None,
        attachments=[
            TelegramAttachment(
                kind="document",
                telegram_file_id="file-1",
                telegram_file_unique_id="unique-1",
                file_name="nota.pdf",
                mime_type="application/pdf",
                size_bytes=1024,
            )
        ],
    )
    download = TelegramAttachmentDownload(
        attachment=message.attachments[0],
        telegram_file_path="documents/nota.pdf",
        content=b"pdf",
        sha256="abc123",
    )
    return repository.save(
        message=message,
        raw_update={"update_id": 10},
        downloads=[download],
    )


def _write_instructions_and_skill(tmp_path: Path) -> Path:
    instructions_path = tmp_path / "AGENTS.md"
    instructions_path.write_text("Use o schema do projeto.", encoding="utf-8")
    skill_dir = tmp_path / ".agents" / "skills" / "fake-skill"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: fake-skill\n"
        "description: Skill de teste para o agente.\n"
        "---\n",
        encoding="utf-8",
    )
    return instructions_path

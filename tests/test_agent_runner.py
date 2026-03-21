from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from esf_agent_service.application.agent_runtime import (
    AgentExecutionRequest,
    AgentRequestAttachment,
    AgentSkillReference,
)
from esf_agent_service.cli.agent_runner import build_codex_command, iter_image_attachments


def test_iter_image_attachments_keeps_only_existing_images(tmp_path: Path) -> None:
    image_path = tmp_path / "nota.jpg"
    image_path.write_bytes(b"jpg")
    pdf_path = tmp_path / "nota.pdf"
    pdf_path.write_bytes(b"pdf")

    request = _build_request(
        tmp_path,
        attachments=[
            AgentRequestAttachment(
                kind="photo",
                file_name="nota.jpg",
                mime_type="image/jpeg",
                size_bytes=3,
                local_path=str(image_path),
                sha256="abc",
            ),
            AgentRequestAttachment(
                kind="document",
                file_name="nota.pdf",
                mime_type="application/pdf",
                size_bytes=3,
                local_path=str(pdf_path),
                sha256="def",
            ),
            AgentRequestAttachment(
                kind="document",
                file_name="missing.png",
                mime_type="image/png",
                size_bytes=0,
                local_path=str(tmp_path / "missing.png"),
                sha256="ghi",
            ),
        ],
    )

    assert iter_image_attachments(request) == [str(image_path)]


def test_build_codex_command_uses_project_root_and_output_path(tmp_path: Path) -> None:
    image_path = tmp_path / "nota.png"
    image_path.write_bytes(b"png")
    request = _build_request(
        tmp_path,
        attachments=[
            AgentRequestAttachment(
                kind="photo",
                file_name="nota.png",
                mime_type="image/png",
                size_bytes=3,
                local_path=str(image_path),
                sha256="abc",
            )
        ],
    )

    command = build_codex_command(
        request,
        codex_bin="codex",
        output_path=tmp_path / "last-message.txt",
    )

    assert command[:8] == [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--cd",
        str(tmp_path),
        "--full-auto",
        "--color",
        "never",
    ]
    assert "--ephemeral" in command
    assert "--output-last-message" in command
    assert "--image" in command
    assert command[-1] == "-"


def _build_request(
    tmp_path: Path,
    *,
    attachments: list[AgentRequestAttachment],
) -> AgentExecutionRequest:
    return AgentExecutionRequest(
        chat_id=1,
        message_id=2,
        update_id=3,
        sent_at=datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        normalized_text="compra mercado",
        project_root=str(tmp_path),
        storage_path=str(tmp_path / "storage"),
        message_path=str(tmp_path / "storage" / "message.json"),
        raw_update_path=str(tmp_path / "storage" / "raw_update.json"),
        attachments_dir=str(tmp_path / "storage" / "attachments"),
        attachments=attachments,
        instructions_path=str(tmp_path / "AGENTS.md"),
        skills=[
            AgentSkillReference(
                name="fake-skill",
                path=str(tmp_path / ".agents" / "skills" / "fake-skill" / "SKILL.md"),
                relative_path=".agents/skills/fake-skill/SKILL.md",
                description="Skill de teste para o agente.",
            )
        ],
        prompt="saida do prompt\n",
    )

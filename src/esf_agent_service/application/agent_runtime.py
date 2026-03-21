from __future__ import annotations

import asyncio
import logging
import os
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Literal, Protocol, Sequence

from pydantic import BaseModel, ConfigDict, Field

from esf_agent_service.domain.models import DownloadedTelegramAttachment, StoredInboundMessage

logger = logging.getLogger(__name__)

DEFAULT_SKILLS_SEARCH_ROOTS = (Path(".agents/skills"), Path(".codex/skills"))
SKILL_FRONTMATTER_FIELD_RE = re.compile(r"^(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.+)$")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AgentRequestAttachment(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["photo", "document", "audio", "voice"]
    file_name: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    local_path: str
    sha256: str


class AgentSkillReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    path: str
    relative_path: str
    description: str | None = None


class AgentExecutionRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    chat_id: int
    message_id: int
    update_id: int
    sent_at: datetime
    normalized_text: str
    project_root: str
    storage_path: str
    message_path: str
    raw_update_path: str
    attachments_dir: str
    attachments: list[AgentRequestAttachment] = Field(default_factory=list)
    instructions_path: str
    skills: list[AgentSkillReference] = Field(default_factory=list)
    prompt: str


class AgentExecutionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["completed", "failed", "skipped"]
    detail: str
    command: list[str] = Field(default_factory=list)
    exit_code: int | None = None
    started_at: datetime
    finished_at: datetime
    stdout: str = ""
    stderr: str = ""


class AgentPromptBuilder:
    def __init__(
        self,
        instructions_path: Path,
        skills_search_roots: Sequence[Path] | None = None,
    ) -> None:
        self._instructions_path = instructions_path
        self._skills_search_roots = tuple(skills_search_roots or DEFAULT_SKILLS_SEARCH_ROOTS)

    def build(self, stored_message: StoredInboundMessage) -> AgentExecutionRequest:
        storage_path = Path(stored_message.storage_path)
        message_path = storage_path / "message.json"
        raw_update_path = storage_path / "raw_update.json"
        attachments_dir = storage_path / "attachments"
        instructions_path = self._resolve_path(self._instructions_path)
        project_root = instructions_path.parent
        skills = self._discover_skills(project_root)
        attachments = [
            self._build_attachment(attachment) for attachment in stored_message.attachments
        ]
        prompt = self._render_prompt(
            stored_message=stored_message,
            project_root=project_root,
            instructions_path=instructions_path,
            instructions_exists=instructions_path.is_file(),
            skills=skills,
            message_path=message_path,
            raw_update_path=raw_update_path,
        )
        message = stored_message.message
        return AgentExecutionRequest(
            chat_id=message.chat_id,
            message_id=message.message_id,
            update_id=message.update_id,
            sent_at=message.sent_at,
            normalized_text=message.normalized_text,
            project_root=str(project_root),
            storage_path=str(storage_path),
            message_path=str(message_path),
            raw_update_path=str(raw_update_path),
            attachments_dir=str(attachments_dir),
            attachments=attachments,
            instructions_path=str(instructions_path),
            skills=skills,
            prompt=prompt,
        )

    def _build_attachment(
        self, attachment: DownloadedTelegramAttachment
    ) -> AgentRequestAttachment:
        return AgentRequestAttachment(
            kind=attachment.kind,
            file_name=attachment.file_name,
            mime_type=attachment.mime_type,
            size_bytes=attachment.size_bytes,
            local_path=attachment.local_path,
            sha256=attachment.sha256,
        )

    def _render_prompt(
        self,
        *,
        stored_message: StoredInboundMessage,
        project_root: Path,
        instructions_path: Path,
        instructions_exists: bool,
        skills: list[AgentSkillReference],
        message_path: Path,
        raw_update_path: Path,
    ) -> str:
        message = stored_message.message
        request_path = Path(stored_message.storage_path) / "agent" / "request.json"
        attachment_lines = [
            f"- {attachment.local_path} ({attachment.kind}, sha256={attachment.sha256})"
            for attachment in stored_message.attachments
        ]
        if not attachment_lines:
            attachment_lines.append("- none")

        if instructions_exists:
            instructions_lines = [
                f"- Leia primeiro o arquivo AGENTS.md em: {instructions_path}",
                "- Use o AGENTS.md como fonte principal de instrucoes do projeto.",
            ]
        else:
            logger.warning("Agent instructions file not found: %s", instructions_path)
            instructions_lines = [
                f"- O arquivo AGENTS.md esperado nao foi encontrado em: {instructions_path}",
                "- Se o arquivo continuar ausente, interrompa ou reporte falha em vez de inventar instrucoes.",
            ]

        skill_lines = [
            f"- {skill.name}: {skill.description or 'sem descricao'} | skill_md={skill.path}"
            for skill in skills
        ]
        if not skill_lines:
            skill_lines.append("- nenhuma skill foi descoberta automaticamente no workspace")

        return "\n".join(
            [
                "Voce esta executando uma tarefa do projeto ESF_agent.",
                "Abra os arquivos do workspace quando necessario e nao invente contexto ausente.",
                "",
                "## Instrucoes de inicio",
                *instructions_lines,
                "- Consulte apenas os SKILL.md necessarios a partir do catalogo abaixo.",
                "- Considere o texto do usuario e os anexos juntos.",
                "- So persista em ESF.ods se o usuario pedir explicitamente.",
                "- Se faltar informacao obrigatoria, responda pedindo esclarecimento em vez de inventar.",
                "",
                "## Contexto da mensagem",
                f"- project_root: {project_root}",
                f"- chat_id: {message.chat_id}",
                f"- message_id: {message.message_id}",
                f"- update_id: {message.update_id}",
                f"- sent_at: {message.sent_at.isoformat()}",
                f"- storage_path: {stored_message.storage_path}",
                f"- request_json: {request_path}",
                f"- message_json: {message_path}",
                f"- raw_update_json: {raw_update_path}",
                "",
                "## Texto normalizado do usuario",
                message.normalized_text or "(sem texto)",
                "",
                "## Anexos locais",
                *attachment_lines,
                "",
                "## Catalogo de skills disponiveis",
                *skill_lines,
                "",
                "## Tarefa",
                "Leia o AGENTS.md, abra apenas as skills relevantes e execute a tarefa pedida pelo usuario.",
                "Responda somente com o resultado final da tarefa.",
            ]
        ).strip() + "\n"

    def _discover_skills(self, project_root: Path) -> list[AgentSkillReference]:
        skills: list[AgentSkillReference] = []
        seen_paths: set[Path] = set()
        for search_root in self._resolved_skill_roots(project_root):
            if not search_root.exists():
                continue
            for skill_md in sorted(search_root.rglob("SKILL.md")):
                skill_path = skill_md.resolve()
                if skill_path in seen_paths:
                    continue
                try:
                    metadata = self._read_skill_metadata(skill_path)
                except OSError as exc:
                    logger.warning("Failed to read skill metadata from %s: %s", skill_path, exc)
                    continue
                skills.append(
                    AgentSkillReference(
                        name=metadata.get("name") or skill_path.parent.name,
                        path=str(skill_path),
                        relative_path=self._relative_to_project(project_root, skill_path),
                        description=metadata.get("description"),
                    )
                )
                seen_paths.add(skill_path)
        return skills

    def _resolved_skill_roots(self, project_root: Path) -> list[Path]:
        roots: list[Path] = []
        for root in self._skills_search_roots:
            resolved = self._resolve_path(root, base_dir=project_root)
            if resolved not in roots:
                roots.append(resolved)
        return roots

    def _read_skill_metadata(self, skill_path: Path) -> dict[str, str]:
        raw_text = skill_path.read_text(encoding="utf-8")
        metadata = self._parse_frontmatter(raw_text)
        if "description" not in metadata:
            fallback = self._extract_description_from_body(raw_text)
            if fallback:
                metadata["description"] = fallback
        return metadata

    def _parse_frontmatter(self, raw_text: str) -> dict[str, str]:
        lines = raw_text.splitlines()
        if not lines or lines[0].strip() != "---":
            return {}

        metadata: dict[str, str] = {}
        for line in lines[1:]:
            stripped = line.strip()
            if stripped == "---":
                break
            match = SKILL_FRONTMATTER_FIELD_RE.match(stripped)
            if match is None:
                continue
            metadata[match.group("key")] = match.group("value").strip().strip("\"'")
        return metadata

    def _extract_description_from_body(self, raw_text: str) -> str | None:
        in_frontmatter = False
        frontmatter_closed = False
        for line in raw_text.splitlines():
            stripped = line.strip()
            if not frontmatter_closed and stripped == "---":
                in_frontmatter = not in_frontmatter
                if not in_frontmatter:
                    frontmatter_closed = True
                continue
            if in_frontmatter or not stripped or stripped.startswith("#"):
                continue
            return stripped
        return None

    def _resolve_path(self, path: Path, *, base_dir: Path | None = None) -> Path:
        candidate = path.expanduser()
        if not candidate.is_absolute():
            candidate = (base_dir or Path.cwd()) / candidate
        return candidate.resolve(strict=False)

    def _relative_to_project(self, project_root: Path, path: Path) -> str:
        try:
            return str(path.relative_to(project_root))
        except ValueError:
            return str(path)


class AgentRunner(Protocol):
    async def run(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        ...


class SkippedAgentRunner:
    def __init__(self, detail: str) -> None:
        self._detail = detail

    async def run(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        timestamp = utcnow()
        return AgentExecutionResult(
            status="skipped",
            detail=self._detail,
            command=[],
            exit_code=None,
            started_at=timestamp,
            finished_at=timestamp,
            stdout="",
            stderr="",
        )


class CommandAgentRunner:
    def __init__(
        self,
        *,
        command_template: str,
        workdir: Path,
        timeout_seconds: int,
    ) -> None:
        self._command_template = command_template
        self._workdir = workdir
        self._timeout_seconds = timeout_seconds

    async def run(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        command = self._build_command(request)
        started_at = utcnow()
        env = self._build_env(request)

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._workdir),
                env=env,
            )
        except FileNotFoundError as exc:
            finished_at = utcnow()
            return AgentExecutionResult(
                status="failed",
                detail=str(exc),
                command=command,
                exit_code=None,
                started_at=started_at,
                finished_at=finished_at,
                stdout="",
                stderr="",
            )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(request.prompt.encode("utf-8")),
                timeout=self._timeout_seconds,
            )
        except asyncio.TimeoutError:
            process.kill()
            stdout_bytes, stderr_bytes = await process.communicate()
            finished_at = utcnow()
            return AgentExecutionResult(
                status="failed",
                detail=f"Agent command timed out after {self._timeout_seconds} seconds.",
                command=command,
                exit_code=process.returncode,
                started_at=started_at,
                finished_at=finished_at,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
            )

        finished_at = utcnow()
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        success = process.returncode == 0
        detail = "Agent command completed successfully." if success else "Agent command failed."
        return AgentExecutionResult(
            status="completed" if success else "failed",
            detail=detail,
            command=command,
            exit_code=process.returncode,
            started_at=started_at,
            finished_at=finished_at,
            stdout=stdout,
            stderr=stderr,
        )

    def _build_command(self, request: AgentExecutionRequest) -> list[str]:
        expanded = self._command_template.format(
            request_path=Path(request.storage_path) / "agent" / "request.json",
            prompt_path=Path(request.storage_path) / "agent" / "prompt.txt",
            storage_path=request.storage_path,
            message_path=request.message_path,
            raw_update_path=request.raw_update_path,
            attachments_dir=request.attachments_dir,
        )
        return shlex.split(expanded)

    def _build_env(self, request: AgentExecutionRequest) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            {
                "ESF_AGENT_STORAGE_PATH": request.storage_path,
                "ESF_AGENT_MESSAGE_PATH": request.message_path,
                "ESF_AGENT_RAW_UPDATE_PATH": request.raw_update_path,
                "ESF_AGENT_ATTACHMENTS_DIR": request.attachments_dir,
                "ESF_AGENT_REQUEST_PATH": str(Path(request.storage_path) / "agent" / "request.json"),
                "ESF_AGENT_PROMPT_PATH": str(Path(request.storage_path) / "agent" / "prompt.txt"),
            }
        )
        return env


class BackgroundTaskDispatcher:
    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[Any]] = set()

    def submit(self, *, label: str, coroutine: Awaitable[None]) -> None:
        task = asyncio.create_task(coroutine, name=label)
        self._tasks.add(task)
        task.add_done_callback(self._handle_completion)

    async def aclose(self) -> None:
        if not self._tasks:
            return
        await asyncio.gather(*tuple(self._tasks), return_exceptions=True)

    def _handle_completion(self, task: asyncio.Task[Any]) -> None:
        self._tasks.discard(task)
        try:
            exception = task.exception()
        except asyncio.CancelledError:
            logger.warning("Background task cancelled: %s", task.get_name())
            return

        if exception is not None:
            logger.exception(
                "Background task failed: %s",
                task.get_name(),
                exc_info=exception,
            )

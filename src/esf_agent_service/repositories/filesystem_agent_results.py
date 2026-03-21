from __future__ import annotations

import json
import tempfile
from pathlib import Path

from esf_agent_service.application.agent_runtime import AgentExecutionRequest, AgentExecutionResult


class FilesystemAgentResultsRepository:
    def save_request(self, request: AgentExecutionRequest) -> None:
        agent_dir = self._agent_dir(request.storage_path)
        agent_dir.mkdir(parents=True, exist_ok=True)
        self._write_json_atomic(agent_dir / "request.json", request.model_dump(mode="json"))
        self._write_text_atomic(agent_dir / "prompt.txt", request.prompt)

    def save_result(self, storage_path: str, result: AgentExecutionResult) -> None:
        agent_dir = self._agent_dir(storage_path)
        agent_dir.mkdir(parents=True, exist_ok=True)
        self._write_text_atomic(agent_dir / "stdout.txt", result.stdout)
        self._write_text_atomic(agent_dir / "stderr.txt", result.stderr)
        payload = result.model_dump(mode="json")
        payload["stdout_path"] = str(agent_dir / "stdout.txt")
        payload["stderr_path"] = str(agent_dir / "stderr.txt")
        self._write_json_atomic(agent_dir / "result.json", payload)

    def _agent_dir(self, storage_path: str) -> Path:
        return Path(storage_path) / "agent"

    def _write_json_atomic(self, path: Path, payload: object) -> None:
        raw = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        self._write_text_atomic(path, raw + "\n")

    def _write_text_atomic(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        temp_path.replace(path)

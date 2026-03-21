from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from esf_agent_service.application.agent_runtime import AgentExecutionRequest

IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Codex agent for a persisted ESF Telegram request."
    )
    parser.add_argument(
        "--request",
        type=Path,
        default=None,
        help="Path to the agent request.json artifact. Defaults to ESF_AGENT_REQUEST_PATH.",
    )
    parser.add_argument(
        "--codex-bin",
        default=os.environ.get("ESF_AGENT_CODEX_BIN", "codex"),
        help="Codex executable to invoke.",
    )
    return parser


def build_codex_command(
    request: AgentExecutionRequest,
    *,
    codex_bin: str,
    output_path: Path,
) -> list[str]:
    command = [
        codex_bin,
        "exec",
        "--skip-git-repo-check",
        "--cd",
        request.project_root,
        "--full-auto",
        "--color",
        "never",
        "--ephemeral",
        "--output-last-message",
        str(output_path),
    ]
    for image_path in iter_image_attachments(request):
        command.extend(["--image", image_path])
    command.append("-")
    return command


def iter_image_attachments(request: AgentExecutionRequest) -> list[str]:
    image_paths: list[str] = []
    for attachment in request.attachments:
        local_path = Path(attachment.local_path)
        if not local_path.is_file():
            continue
        if attachment.kind == "photo" or _looks_like_image(local_path, attachment.mime_type):
            image_paths.append(str(local_path))
    return image_paths


def load_request(path: Path) -> AgentExecutionRequest:
    return AgentExecutionRequest.model_validate_json(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    request_path = args.request or _request_path_from_env()
    if request_path is None:
        parser.error("--request is required when ESF_AGENT_REQUEST_PATH is not set.")

    request = load_request(request_path)
    prompt = sys.stdin.read() or request.prompt
    output_path = _temporary_output_path()
    command = build_codex_command(
        request,
        codex_bin=args.codex_bin,
        output_path=output_path,
    )

    try:
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                cwd=request.project_root,
                stdout=sys.stderr,
                stderr=sys.stderr,
                check=False,
            )
        except FileNotFoundError as exc:
            print(f"Unable to launch Codex CLI: {exc}", file=sys.stderr)
            return 127
        if output_path.is_file():
            final_output = output_path.read_text(encoding="utf-8")
            if final_output:
                sys.stdout.write(final_output)
                if not final_output.endswith("\n"):
                    sys.stdout.write("\n")
        return completed.returncode
    finally:
        if output_path.exists():
            output_path.unlink()


def _request_path_from_env() -> Path | None:
    raw_value = os.environ.get("ESF_AGENT_REQUEST_PATH")
    if not raw_value:
        return None
    return Path(raw_value)


def _temporary_output_path() -> Path:
    with tempfile.NamedTemporaryFile(prefix="esf-agent-", suffix=".txt", delete=False) as handle:
        return Path(handle.name)


def _looks_like_image(path: Path, mime_type: str | None) -> bool:
    if mime_type and mime_type.startswith("image/"):
        return True
    return path.suffix.lower() in IMAGE_SUFFIXES


if __name__ == "__main__":
    raise SystemExit(main())

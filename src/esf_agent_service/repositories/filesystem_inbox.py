from __future__ import annotations

import json
import tempfile
from datetime import timezone
from pathlib import Path
import re

from esf_agent_service.domain.models import (
    DownloadedTelegramAttachment,
    InboundTelegramMessage,
    StoredInboundMessage,
    TelegramAttachmentDownload,
)

INVALID_FILENAME_CHARS_RE = re.compile(r"[^A-Za-z0-9._-]+")


class FilesystemInboxRepository:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        *,
        message: InboundTelegramMessage,
        raw_update: dict,
        downloads: list[TelegramAttachmentDownload],
    ) -> StoredInboundMessage:
        message_dir = self._build_message_dir(message)
        message_dir.mkdir(parents=True, exist_ok=True)

        message_file = message_dir / "message.json"
        duplicate = message_file.exists()

        self._write_json_atomic(message_file, message.model_dump(mode="json"))
        self._write_json_atomic(message_dir / "raw_update.json", raw_update)

        stored_attachments: list[DownloadedTelegramAttachment] = []
        if downloads:
            attachments_dir = message_dir / "attachments"
            attachments_dir.mkdir(parents=True, exist_ok=True)
            for download in downloads:
                file_name = self._resolve_attachment_name(download)
                local_path = attachments_dir / file_name
                self._write_bytes_atomic(local_path, download.content)
                stored_attachments.append(
                    DownloadedTelegramAttachment(
                        kind=download.attachment.kind,
                        telegram_file_id=download.attachment.telegram_file_id,
                        telegram_file_unique_id=download.attachment.telegram_file_unique_id,
                        file_name=download.attachment.file_name,
                        mime_type=download.attachment.mime_type,
                        size_bytes=download.attachment.size_bytes,
                        telegram_file_path=download.telegram_file_path,
                        local_path=str(local_path),
                        sha256=download.sha256,
                    )
                )

        return StoredInboundMessage(
            message=message,
            storage_path=str(message_dir),
            duplicate=duplicate,
            attachments=stored_attachments,
        )

    def _build_message_dir(self, message: InboundTelegramMessage) -> Path:
        sent_at = message.sent_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return (
            self._root
            / f"chat_{message.chat_id}"
            / f"{sent_at}__m{message.message_id}__u{message.update_id}"
        )

    def _resolve_attachment_name(self, download: TelegramAttachmentDownload) -> str:
        file_name = download.attachment.file_name or f"{download.attachment.kind}.bin"
        safe_name = INVALID_FILENAME_CHARS_RE.sub("_", file_name)
        return safe_name.strip("._") or f"{download.attachment.kind}.bin"

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

    def _write_bytes_atomic(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, delete=False) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        temp_path.replace(path)

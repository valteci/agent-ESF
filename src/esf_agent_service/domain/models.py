from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TelegramAttachment(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["photo", "document", "audio", "voice"]
    telegram_file_id: str
    telegram_file_unique_id: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None


@dataclass(frozen=True, slots=True)
class TelegramAttachmentDownload:
    attachment: TelegramAttachment
    telegram_file_path: str
    content: bytes
    sha256: str


class DownloadedTelegramAttachment(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["photo", "document", "audio", "voice"]
    telegram_file_id: str
    telegram_file_unique_id: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    telegram_file_path: str
    local_path: str
    sha256: str


class InboundTelegramMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    update_id: int
    update_type: str
    message_id: int
    chat_id: int
    chat_type: str
    sender_user_id: int | None = None
    sender_username: str | None = None
    sender_first_name: str | None = None
    sent_at: datetime
    text: str = ""
    caption: str = ""
    media_group_id: str | None = None
    attachments: list[TelegramAttachment] = Field(default_factory=list)

    @property
    def normalized_text(self) -> str:
        return "\n\n".join(part for part in (self.text.strip(), self.caption.strip()) if part)


class StoredInboundMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    message: InboundTelegramMessage
    storage_path: str
    duplicate: bool
    attachments: list[DownloadedTelegramAttachment] = Field(default_factory=list)


class IngestionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["stored", "ignored", "duplicate"]
    detail: str
    storage_path: str | None = None

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from esf_agent_service.domain.models import InboundTelegramMessage, TelegramAttachment


class TelegramUpdateParser:
    def parse(self, update: dict[str, Any]) -> InboundTelegramMessage | None:
        update_id = update.get("update_id")
        if update_id is None:
            return None

        update_type, message = self._extract_message_payload(update)
        if message is None:
            return None

        chat = message.get("chat") or {}
        sender = message.get("from") or {}
        attachments = self._extract_attachments(message)
        message_id = message.get("message_id")
        chat_id = chat.get("id")

        timestamp = message.get("date")
        if timestamp is None or message_id is None or chat_id is None:
            return None

        return InboundTelegramMessage(
            update_id=int(update_id),
            update_type=update_type,
            message_id=int(message_id),
            chat_id=int(chat_id),
            chat_type=str(chat.get("type", "private")),
            sender_user_id=self._to_optional_int(sender.get("id")),
            sender_username=self._to_optional_str(sender.get("username")),
            sender_first_name=self._to_optional_str(sender.get("first_name")),
            sent_at=datetime.fromtimestamp(int(timestamp), tz=timezone.utc),
            text=self._to_optional_str(message.get("text")) or "",
            caption=self._to_optional_str(message.get("caption")) or "",
            media_group_id=self._to_optional_str(message.get("media_group_id")),
            attachments=attachments,
        )

    def _extract_message_payload(self, update: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
        for candidate in ("message", "edited_message"):
            payload = update.get(candidate)
            if isinstance(payload, dict):
                return candidate, payload
        return "unsupported", None

    def _extract_attachments(self, message: dict[str, Any]) -> list[TelegramAttachment]:
        attachments: list[TelegramAttachment] = []

        photos = message.get("photo")
        if isinstance(photos, list) and photos:
            largest_photo = max(
                photos,
                key=lambda item: (
                    int(item.get("width", 0)) * int(item.get("height", 0)),
                    int(item.get("file_size", 0)),
                ),
            )
            attachments.append(
                TelegramAttachment(
                    kind="photo",
                    telegram_file_id=str(largest_photo["file_id"]),
                    telegram_file_unique_id=self._to_optional_str(
                        largest_photo.get("file_unique_id")
                    ),
                    file_name=self._build_photo_name(largest_photo),
                    size_bytes=self._to_optional_int(largest_photo.get("file_size")),
                )
            )

        document = message.get("document")
        if isinstance(document, dict):
            attachments.append(
                TelegramAttachment(
                    kind="document",
                    telegram_file_id=str(document["file_id"]),
                    telegram_file_unique_id=self._to_optional_str(document.get("file_unique_id")),
                    file_name=self._to_optional_str(document.get("file_name")),
                    mime_type=self._to_optional_str(document.get("mime_type")),
                    size_bytes=self._to_optional_int(document.get("file_size")),
                )
            )

        audio = message.get("audio")
        if isinstance(audio, dict):
            attachments.append(
                TelegramAttachment(
                    kind="audio",
                    telegram_file_id=str(audio["file_id"]),
                    telegram_file_unique_id=self._to_optional_str(audio.get("file_unique_id")),
                    file_name=self._to_optional_str(audio.get("file_name")),
                    mime_type=self._to_optional_str(audio.get("mime_type")),
                    size_bytes=self._to_optional_int(audio.get("file_size")),
                )
            )

        voice = message.get("voice")
        if isinstance(voice, dict):
            attachments.append(
                TelegramAttachment(
                    kind="voice",
                    telegram_file_id=str(voice["file_id"]),
                    telegram_file_unique_id=self._to_optional_str(voice.get("file_unique_id")),
                    file_name=self._build_voice_name(voice),
                    mime_type=self._to_optional_str(voice.get("mime_type")),
                    size_bytes=self._to_optional_int(voice.get("file_size")),
                )
            )

        return attachments

    def _build_photo_name(self, photo: dict[str, Any]) -> str:
        unique_id = self._to_optional_str(photo.get("file_unique_id")) or "telegram-photo"
        return f"{unique_id}.jpg"

    def _build_voice_name(self, voice: dict[str, Any]) -> str:
        unique_id = self._to_optional_str(voice.get("file_unique_id")) or "telegram-voice"
        return f"{unique_id}.ogg"

    def _to_optional_int(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        return int(value)

    def _to_optional_str(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        return str(value)

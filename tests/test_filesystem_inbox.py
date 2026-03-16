from __future__ import annotations

import json
from datetime import datetime, timezone

from esf_agent_service.domain.models import InboundTelegramMessage
from esf_agent_service.repositories.filesystem_inbox import FilesystemInboxRepository


def test_save_message_creates_expected_artifacts(tmp_path) -> None:
    repository = FilesystemInboxRepository(tmp_path)
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
        text="hello",
        caption="",
        media_group_id=None,
        attachments=[],
    )

    stored = repository.save(message=message, raw_update={"update_id": 10}, downloads=[])

    assert stored.duplicate is False
    message_file = tmp_path / "chat_30" / "20240102T030405Z__m20__u10" / "message.json"
    raw_update_file = message_file.with_name("raw_update.json")
    assert message_file.is_file()
    assert raw_update_file.is_file()

    payload = json.loads(message_file.read_text(encoding="utf-8"))
    assert payload["chat_id"] == 30
    assert payload["text"] == "hello"

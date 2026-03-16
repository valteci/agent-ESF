from __future__ import annotations

from esf_agent_service.integrations.telegram.parser import TelegramUpdateParser


def test_parse_text_message() -> None:
    parser = TelegramUpdateParser()
    update = {
        "update_id": 101,
        "message": {
            "message_id": 7,
            "date": 1_717_000_000,
            "chat": {"id": 10, "type": "private"},
            "from": {"id": 20, "first_name": "Ada", "username": "ada"},
            "text": "compra mercado",
        },
    }

    message = parser.parse(update)

    assert message is not None
    assert message.update_id == 101
    assert message.chat_id == 10
    assert message.sender_user_id == 20
    assert message.text == "compra mercado"
    assert message.attachments == []


def test_parse_document_with_caption() -> None:
    parser = TelegramUpdateParser()
    update = {
        "update_id": 102,
        "message": {
            "message_id": 8,
            "date": 1_717_000_123,
            "chat": {"id": 30, "type": "private"},
            "from": {"id": 40, "first_name": "Lin", "username": "lin"},
            "caption": "nota fiscal do mes",
            "document": {
                "file_id": "file-123",
                "file_unique_id": "uniq-123",
                "file_name": "nota.pdf",
                "mime_type": "application/pdf",
                "file_size": 2048,
            },
        },
    }

    message = parser.parse(update)

    assert message is not None
    assert message.caption == "nota fiscal do mes"
    assert len(message.attachments) == 1
    assert message.attachments[0].kind == "document"
    assert message.attachments[0].file_name == "nota.pdf"

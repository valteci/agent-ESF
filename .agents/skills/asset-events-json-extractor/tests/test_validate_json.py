import json
import sys
from pathlib import Path

import pytest


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_json import (  # noqa: E402
    main,
    validate_json_file,
    validate_json_text,
    validate_payload,
    validate_transaction,
)


def test_validate_transaction_with_valid_data():
    transaction = {
        "from": "ITUB4_yeld",
        "to": "rico",
        "amount": "10.00",
        "type": "create batch",
        "timestamp": "15-03-2026",
        "obs": "Recebimento de dividendos de ITUB4 na rico",
    }

    errors = validate_transaction(transaction, 0)

    assert errors == []


def test_validate_payload_with_single_valid_transaction():
    payload = {
        "transactions": [
            {
                "from": "qtde__bens",
                "to": "ETHEREUM_QTDE",
                "amount": "0.01500000",
                "type": "buy",
                "timestamp": "15-03-2026",
                "obs": "Recebimento de recompensa de staking em ETHEREUM",
            }
        ]
    }

    errors = validate_payload(payload)

    assert errors == []


def test_validate_payload_with_empty_transactions_is_valid():
    payload = {"transactions": []}

    errors = validate_payload(payload)

    assert errors == []


def test_validate_payload_root_must_be_object():
    payload = ["not", "an", "object"]

    errors = validate_payload(payload)

    assert errors == ["root must be an object"]


def test_validate_payload_rejects_missing_transactions_key():
    payload = {}

    errors = validate_payload(payload)

    assert errors == ["root is missing required keys: transactions"]


def test_validate_payload_rejects_extra_root_keys():
    payload = {
        "transactions": [],
        "foo": "bar",
    }

    errors = validate_payload(payload)

    assert errors == ["root contains unexpected keys: foo"]


def test_validate_payload_rejects_transactions_when_not_a_list():
    payload = {
        "transactions": "not-a-list",
    }

    errors = validate_payload(payload)

    assert errors == ["transactions must be a list"]


def test_validate_transaction_rejects_missing_keys():
    transaction = {
        "from": "ITUB4_yeld",
        "to": "rico",
        "amount": "10.00",
        "type": "create batch",
        "timestamp": "15-03-2026",
    }

    errors = validate_transaction(transaction, 0)

    assert errors == ["transactions[0] is missing required keys: obs"]


def test_validate_transaction_rejects_extra_keys():
    transaction = {
        "from": "ITUB4_yeld",
        "to": "rico",
        "amount": "10.00",
        "type": "create batch",
        "timestamp": "15-03-2026",
        "obs": "Recebimento de dividendos de ITUB4 na rico",
        "category": "provento",
    }

    errors = validate_transaction(transaction, 0)

    assert errors == ["transactions[0] contains unexpected keys: category"]


def test_validate_transaction_rejects_non_string_values():
    transaction = {
        "from": "ITUB4_yeld",
        "to": "rico",
        "amount": 10.0,
        "type": "create batch",
        "timestamp": "15-03-2026",
        "obs": "Recebimento de dividendos de ITUB4 na rico",
    }

    errors = validate_transaction(transaction, 0)

    assert errors == ["transactions[0].amount must be a string, got float"]


def test_validate_transaction_rejects_non_object_transaction():
    transaction = "not-an-object"

    errors = validate_transaction(transaction, 2)

    assert errors == ["transactions[2] must be an object"]


def test_validate_json_text_rejects_invalid_json():
    json_text = '{"transactions": [}'

    errors = validate_json_text(json_text)

    assert len(errors) == 1
    assert errors[0].startswith("invalid JSON:")


def test_validate_json_file_with_valid_content(tmp_path: Path):
    payload = {
        "transactions": [
            {
                "from": "qtde__bens",
                "to": "PETR4_QTDE",
                "amount": "10",
                "type": "buy",
                "timestamp": "15-03-2026",
                "obs": "Ajuste manual com acrescimo de 10 acoes de PETR4",
            }
        ]
    }

    file_path = tmp_path / "valid.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    errors = validate_json_file(file_path)

    assert errors == []


def test_validate_json_file_with_invalid_content(tmp_path: Path):
    payload = {
        "transactions": [
            {
                "from": "qtde__bens",
                "to": "PETR4_QTDE",
                "amount": "10",
                "type": "buy",
                "timestamp": "15-03-2026",
            }
        ]
    }

    file_path = tmp_path / "invalid.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    errors = validate_json_file(file_path)

    assert errors == ["transactions[0] is missing required keys: obs"]


def test_main_returns_zero_for_valid_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    payload = {
        "transactions": [
            {
                "from": "MXRF11_yeld",
                "to": "xp",
                "amount": "25.90",
                "type": "create batch",
                "timestamp": "15-03-2026",
                "obs": "Recebimento de rendimento de MXRF11 na xp",
            }
        ]
    }

    file_path = tmp_path / "valid.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = main([str(file_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "VALID"


def test_main_returns_one_for_invalid_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    payload = {
        "transactions": [
            {
                "from": "MXRF11_yeld",
                "to": "xp",
                "amount": "25.90",
                "type": "create batch",
                "timestamp": "15-03-2026",
                "obs": 123,
            }
        ]
    }

    file_path = tmp_path / "invalid.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = main([str(file_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "INVALID" in captured.out
    assert "transactions[0].obs must be a string, got int" in captured.out

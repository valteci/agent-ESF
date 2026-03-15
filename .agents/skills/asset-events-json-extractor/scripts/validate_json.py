#!/usr/bin/env python3
"""
Validador do JSON gerado pela skill `asset-events-json-extractor`.

Schema esperado:

{
    "transactions": [
        {
            "from": "...",
            "to": "...",
            "amount": "...",
            "type": "...",
            "timestamp": "...",
            "obs": "..."
        }
    ]
}

Regras validadas:
- O JSON raiz deve ser um objeto
- O JSON raiz deve conter exatamente a chave "transactions"
- "transactions" deve ser uma lista
- Cada item da lista deve ser um objeto
- Cada objeto de transacao deve conter exatamente as chaves:
  from, to, amount, type, timestamp, obs
- Todos os valores dessas chaves devem ser strings
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_TRANSACTION_KEYS = (
    "from",
    "to",
    "amount",
    "type",
    "timestamp",
    "obs",
)

ROOT_KEYS = ("transactions",)


def validate_transaction(transaction: Any, index: int) -> list[str]:
    """
    Valida uma transacao individual.

    Args:
        transaction: Objeto da transacao.
        index: Indice da transacao dentro da lista.

    Returns:
        Lista de erros encontrados.
    """
    errors: list[str] = []

    if not isinstance(transaction, dict):
        return [f"transactions[{index}] must be an object"]

    actual_keys = set(transaction.keys())
    required_keys = set(REQUIRED_TRANSACTION_KEYS)

    missing_keys = required_keys - actual_keys
    extra_keys = actual_keys - required_keys

    if missing_keys:
        missing_sorted = ", ".join(sorted(missing_keys))
        errors.append(
            f"transactions[{index}] is missing required keys: {missing_sorted}"
        )

    if extra_keys:
        extra_sorted = ", ".join(sorted(extra_keys))
        errors.append(
            f"transactions[{index}] contains unexpected keys: {extra_sorted}"
        )

    for key in REQUIRED_TRANSACTION_KEYS:
        if key not in transaction:
            continue

        value = transaction[key]
        if not isinstance(value, str):
            errors.append(
                f"transactions[{index}].{key} must be a string, "
                f"got {type(value).__name__}"
            )

    return errors


def validate_payload(payload: Any) -> list[str]:
    """
    Valida o payload inteiro.

    Args:
        payload: JSON ja desserializado em objeto Python.

    Returns:
        Lista de erros encontrados. Lista vazia significa payload valido.
    """
    errors: list[str] = []

    if not isinstance(payload, dict):
        return ["root must be an object"]

    actual_root_keys = set(payload.keys())
    expected_root_keys = set(ROOT_KEYS)

    missing_root_keys = expected_root_keys - actual_root_keys
    extra_root_keys = actual_root_keys - expected_root_keys

    if missing_root_keys:
        missing_sorted = ", ".join(sorted(missing_root_keys))
        errors.append(f"root is missing required keys: {missing_sorted}")

    if extra_root_keys:
        extra_sorted = ", ".join(sorted(extra_root_keys))
        errors.append(f"root contains unexpected keys: {extra_sorted}")

    if "transactions" not in payload:
        return errors

    transactions = payload["transactions"]

    if not isinstance(transactions, list):
        errors.append("transactions must be a list")
        return errors

    for index, transaction in enumerate(transactions):
        errors.extend(validate_transaction(transaction, index))

    return errors


def validate_json_text(json_text: str) -> list[str]:
    """
    Valida um texto JSON.

    Args:
        json_text: Conteudo JSON em string.

    Returns:
        Lista de erros encontrados.
    """
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}"]

    return validate_payload(payload)


def validate_json_file(file_path: str | Path) -> list[str]:
    """
    Valida um arquivo JSON.

    Args:
        file_path: Caminho para o arquivo JSON.

    Returns:
        Lista de erros encontrados.
    """
    path = Path(file_path)

    try:
        json_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"file not found: {path}"]
    except OSError as exc:
        return [f"could not read file '{path}': {exc}"]

    return validate_json_text(json_text)


def main(argv: list[str] | None = None) -> int:
    """
    Interface de linha de comando.

    Uso:
      python validate_json.py arquivo.json
      cat arquivo.json | python validate_json.py
    """
    parser = argparse.ArgumentParser(
        description="Valida o JSON gerado pela skill asset-events-json-extractor."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Caminho para o arquivo JSON. Se omitido, le do stdin.",
    )

    args = parser.parse_args(argv)

    if args.file:
        errors = validate_json_file(args.file)
    else:
        json_text = sys.stdin.read()
        errors = validate_json_text(json_text)

    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

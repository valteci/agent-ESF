#!/usr/bin/env python3

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "calcext": "urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0",
}
TARGET_SHEET = "F26"
EXPECTED_HEADERS = ("from", "to", "amount", "type", "timestamp", "id", "Obs.:")
ROOT_KEY_CANDIDATES = ("transactions", "transactinos")
REQUIRED_TRANSACTION_KEYS = ("from", "to", "amount", "type", "timestamp", "obs")
ODS_MIMETYPE = "application/vnd.oasis.opendocument.spreadsheet"
DOCUMENT_CONTENT_START_RE = re.compile(br"<office:document-content\b[^>]*>", re.DOTALL)
XML_DECLARATION_RE = re.compile(br"^\s*<\?xml.*?\?>\s*", re.DOTALL)


for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


@dataclass(frozen=True)
class ParsedTransaction:
    from_value: str
    to_value: str
    amount_value: Decimal
    amount_text: str
    type_value: str
    date_value: str
    date_text: str
    obs_value: str


class OdsInsertError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Insere transacoes JSON na aba F26 da planilha ODS do projeto."
    )
    parser.add_argument(
        "--json",
        required=True,
        dest="json_input",
        help="JSON bruto ou caminho para um arquivo JSON.",
    )
    parser.add_argument(
        "--ods-path",
        dest="ods_path",
        help="Caminho da planilha ODS. Se omitido, usa ESF.ods na raiz.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        workbook_path = resolve_workbook_path(args.ods_path)
        payload = load_json_argument(args.json_input)
        transactions = parse_transactions(payload)
        if not transactions:
            raise OdsInsertError("O JSON nao contem transacoes para inserir.")
        insert_transactions(workbook_path, transactions)
    except OdsInsertError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1

    print(
        f"{len(transactions)} transacao(oes) inserida(s) em {TARGET_SHEET} de {workbook_path.name}."
    )
    return 0


def resolve_workbook_path(explicit_path: str | None) -> Path:
    if explicit_path:
        path = Path(explicit_path).expanduser().resolve()
        if not path.is_file():
            raise OdsInsertError(f"Planilha nao encontrada: {path}")
        return path

    path = (Path.cwd() / "ESF.ods").resolve()
    if path.is_file():
        return path
    raise OdsInsertError("Nenhuma planilha encontrada na raiz atual. Esperado: ESF.ods.")


def load_json_argument(argument: str) -> object:
    path = Path(argument)
    if path.is_file():
        raw = path.read_text(encoding="utf-8")
    else:
        raw = argument

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OdsInsertError(f"JSON invalido: {exc}") from exc


def parse_transactions(payload: object) -> list[ParsedTransaction]:
    if not isinstance(payload, dict):
        raise OdsInsertError("O JSON raiz deve ser um objeto.")

    transactions_value = None
    for key in ROOT_KEY_CANDIDATES:
        if key in payload:
            transactions_value = payload[key]
            break

    if transactions_value is None:
        raise OdsInsertError("O JSON deve conter a chave transactions.")
    if not isinstance(transactions_value, list):
        raise OdsInsertError("A chave transactions deve conter uma lista.")

    parsed: list[ParsedTransaction] = []
    for index, item in enumerate(transactions_value, start=1):
        if not isinstance(item, dict):
            raise OdsInsertError(f"Transacao {index}: cada item deve ser um objeto.")
        missing = [key for key in REQUIRED_TRANSACTION_KEYS if key not in item]
        if missing:
            missing_text = ", ".join(missing)
            raise OdsInsertError(f"Transacao {index}: faltam campos obrigatorios: {missing_text}.")

        amount = parse_decimal(coerce_string(item["amount"]), index)
        parsed_date = parse_date(coerce_string(item["timestamp"]), index)

        parsed.append(
            ParsedTransaction(
                from_value=coerce_string(item["from"]),
                to_value=coerce_string(item["to"]),
                amount_value=amount,
                amount_text=format_amount_text(amount),
                type_value=coerce_string(item["type"]),
                date_value=parsed_date.strftime("%Y-%m-%d"),
                date_text=parsed_date.strftime("%d/%m/%y"),
                obs_value=coerce_string(item["obs"]),
            )
        )
    return parsed


def coerce_string(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_decimal(raw_value: str, index: int) -> Decimal:
    text = raw_value.strip().replace("R$", "").replace(" ", "")
    if not text:
        raise OdsInsertError(f"Transacao {index}: amount vazio.")

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            normalized = text.replace(".", "").replace(",", ".")
        else:
            normalized = text.replace(",", "")
    elif "," in text:
        normalized = text.replace(".", "").replace(",", ".")
    else:
        normalized = text

    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise OdsInsertError(f"Transacao {index}: amount invalido: {raw_value!r}.") from exc


def format_amount_text(amount: Decimal) -> str:
    value = decimal_to_string(amount)
    return value.replace(".", ",")


def decimal_to_string(amount: Decimal) -> str:
    text = format(amount, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def parse_date(raw_value: str, index: int) -> datetime:
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw_value, fmt)
        except ValueError:
            continue
    raise OdsInsertError(
        f"Transacao {index}: timestamp invalido: {raw_value!r}. Formatos aceitos: DD-MM-YYYY, DD/MM/YYYY, DD/MM/YY, YYYY-MM-DD."
    )


def insert_transactions(workbook_path: Path, transactions: Iterable[ParsedTransaction]) -> None:
    with zipfile.ZipFile(workbook_path, "r") as source_zip:
        ensure_ods_archive(source_zip, workbook_path)
        content = source_zip.read("content.xml")
        updated_content = update_content_xml(content, list(transactions))
        write_updated_archive(workbook_path, source_zip, updated_content)


def ensure_ods_archive(source_zip: zipfile.ZipFile, workbook_path: Path) -> None:
    try:
        mimetype = source_zip.read("mimetype").decode("utf-8")
    except KeyError as exc:
        raise OdsInsertError(f"{workbook_path.name} nao parece ser uma planilha ODS valida.") from exc
    if mimetype != ODS_MIMETYPE:
        raise OdsInsertError(
            f"{workbook_path.name} nao tem mimetype de planilha ODS: {mimetype!r}."
        )


def update_content_xml(content: bytes, transactions: list[ParsedTransaction]) -> bytes:
    root = ET.fromstring(content)
    table = find_target_table(root)
    header_index = find_header_row_index(table)
    template_row = find_template_row(table, header_index)
    insertion_index = find_insertion_index(table, header_index)
    total_columns = count_row_columns(template_row)
    row_elements = list(table.findall("table:table-row", NS))
    child_elements = list(table)

    if insertion_index < len(row_elements):
        child_insertion_index = child_elements.index(row_elements[insertion_index])
    else:
        child_insertion_index = len(child_elements)

    for offset, transaction in enumerate(transactions):
        new_row = build_transaction_row(template_row, total_columns, transaction)
        table.insert(child_insertion_index + offset, new_row)

    shrink_following_blank_rows(table, insertion_index + len(transactions), len(transactions))
    return serialize_content_xml(root, content)


def serialize_content_xml(root: ET.Element, original_content: bytes) -> bytes:
    register_original_namespaces(original_content)
    serialized = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return preserve_original_document_header(original_content, serialized)


def register_original_namespaces(content: bytes) -> None:
    seen: set[tuple[str, str]] = set()
    for _, namespace in ET.iterparse(io.BytesIO(content), events=("start-ns",)):
        prefix, uri = namespace
        normalized_prefix = prefix or ""
        key = (normalized_prefix, uri)
        if key in seen:
            continue
        seen.add(key)
        try:
            ET.register_namespace(normalized_prefix, uri)
        except ValueError:
            continue


def preserve_original_document_header(original_content: bytes, serialized_content: bytes) -> bytes:
    original_root = DOCUMENT_CONTENT_START_RE.search(original_content)
    serialized_root = DOCUMENT_CONTENT_START_RE.search(serialized_content)
    if original_root is None or serialized_root is None:
        return serialized_content

    updated = (
        serialized_content[: serialized_root.start()]
        + original_root.group(0)
        + serialized_content[serialized_root.end() :]
    )

    original_declaration = XML_DECLARATION_RE.match(original_content)
    serialized_declaration = XML_DECLARATION_RE.match(updated)
    if original_declaration is None or serialized_declaration is None:
        return updated

    return original_declaration.group(0) + updated[serialized_declaration.end() :]


def find_target_table(root: ET.Element) -> ET.Element:
    spreadsheet = root.find("office:body/office:spreadsheet", NS)
    if spreadsheet is None:
        raise OdsInsertError("Nao foi possivel localizar o conteudo da planilha no arquivo ODS.")

    table_name_attr = qname("table", "name")
    for table in spreadsheet.findall("table:table", NS):
        if table.attrib.get(table_name_attr) == TARGET_SHEET:
            return table
    raise OdsInsertError(f"A aba {TARGET_SHEET} nao foi encontrada na planilha.")


def find_header_row_index(table: ET.Element) -> int:
    rows = list(table.findall("table:table-row", NS))
    for index, row in enumerate(rows):
        if tuple(expand_row_text(row, 7)) == EXPECTED_HEADERS:
            return index
    raise OdsInsertError(
        f"Nao foi possivel localizar o cabecalho esperado na aba {TARGET_SHEET}."
    )


def find_template_row(table: ET.Element, header_index: int) -> ET.Element:
    rows = list(table.findall("table:table-row", NS))
    for row in rows[header_index + 1 :]:
        values = expand_row_text(row, 7)
        if any(values[:5]):
            return row
    raise OdsInsertError("Nao foi possivel localizar uma linha modelo de transacao na aba F26.")


def find_insertion_index(table: ET.Element, header_index: int) -> int:
    rows = list(table.findall("table:table-row", NS))
    for index in range(len(rows) - 1, header_index, -1):
        values = expand_row_text(rows[index], 7)
        if is_placeholder_row(values) or is_blank_row(values):
            continue
        return index + 1
    raise OdsInsertError("Nao foi encontrado um ponto seguro de insercao na aba F26.")


def build_transaction_row(
    template_row: ET.Element, total_columns: int, transaction: ParsedTransaction
) -> ET.Element:
    template_cells = list(template_row.findall("table:table-cell", NS))
    if len(template_cells) < 7:
        raise OdsInsertError("Linha modelo da aba F26 nao tem colunas suficientes.")

    row = copy.deepcopy(template_row)
    for child in list(row):
        row.remove(child)

    row.append(make_string_cell(template_cells[0], transaction.from_value))
    row.append(make_string_cell(template_cells[1], transaction.to_value))
    row.append(make_float_cell(template_cells[2], transaction.amount_value, transaction.amount_text))
    row.append(make_string_cell(template_cells[3], transaction.type_value))
    row.append(make_date_cell(template_cells[4], transaction.date_value, transaction.date_text))
    row.append(make_blank_cell(template_cells[5]))
    row.append(make_string_cell(template_cells[6], transaction.obs_value))

    remaining_columns = total_columns - 7
    if remaining_columns > 0:
        row.append(make_repeated_blank_cell(remaining_columns))
    return row


def shrink_following_blank_rows(table: ET.Element, blank_row_index: int, inserted_count: int) -> None:
    rows = list(table.findall("table:table-row", NS))
    if blank_row_index >= len(rows):
        return

    repeated_attr = qname("table", "number-rows-repeated")
    blank_row = rows[blank_row_index]
    repeated = int(blank_row.attrib.get(repeated_attr, "1"))
    if repeated <= inserted_count:
        if repeated == inserted_count:
            table.remove(blank_row)
        return
    blank_row.attrib[repeated_attr] = str(repeated - inserted_count)


def make_string_cell(template_cell: ET.Element, value: str) -> ET.Element:
    cell = base_cell_from_template(template_cell)
    if value:
        cell.attrib[qname("office", "value-type")] = "string"
        cell.attrib[qname("calcext", "value-type")] = "string"
        cell.append(make_text_paragraph(value))
    return cell


def make_float_cell(template_cell: ET.Element, value: Decimal, display_text: str) -> ET.Element:
    cell = base_cell_from_template(template_cell)
    cell.attrib[qname("office", "value-type")] = "float"
    cell.attrib[qname("office", "value")] = decimal_to_string(value)
    cell.attrib[qname("calcext", "value-type")] = "float"
    cell.append(make_text_paragraph(display_text))
    return cell


def make_date_cell(template_cell: ET.Element, iso_date: str, display_text: str) -> ET.Element:
    cell = base_cell_from_template(template_cell)
    cell.attrib[qname("office", "value-type")] = "date"
    cell.attrib[qname("office", "date-value")] = iso_date
    cell.attrib[qname("calcext", "value-type")] = "date"
    cell.append(make_text_paragraph(display_text))
    return cell


def make_blank_cell(template_cell: ET.Element) -> ET.Element:
    return base_cell_from_template(template_cell)


def make_repeated_blank_cell(repetitions: int) -> ET.Element:
    cell = ET.Element(qname("table", "table-cell"))
    cell.attrib[qname("table", "number-columns-repeated")] = str(repetitions)
    return cell


def base_cell_from_template(template_cell: ET.Element) -> ET.Element:
    cell = ET.Element(template_cell.tag)
    style_attr = qname("table", "style-name")
    if style_attr in template_cell.attrib:
        cell.attrib[style_attr] = template_cell.attrib[style_attr]
    return cell


def make_text_paragraph(value: str) -> ET.Element:
    paragraph = ET.Element(qname("text", "p"))
    paragraph.text = value
    return paragraph


def expand_row_text(row: ET.Element, limit: int) -> list[str]:
    values: list[str] = []
    for cell in row.findall("table:table-cell", NS):
        repeated = int(cell.attrib.get(qname("table", "number-columns-repeated"), "1"))
        text = "".join("".join(p.itertext()) for p in cell.findall("text:p", NS))
        values.extend([text] * repeated)
        if len(values) >= limit:
            return values[:limit]
    return values[:limit]


def is_blank_row(values: list[str]) -> bool:
    return not any(value.strip() for value in values)


def is_placeholder_row(values: list[str]) -> bool:
    non_empty = [value.strip() for value in values if value.strip()]
    return bool(non_empty) and all(value == "-" for value in non_empty)


def count_row_columns(row: ET.Element) -> int:
    total = 0
    for cell in row.findall("table:table-cell", NS):
        total += int(cell.attrib.get(qname("table", "number-columns-repeated"), "1"))
    return total


def write_updated_archive(
    workbook_path: Path, source_zip: zipfile.ZipFile, updated_content: bytes
) -> None:
    temp_handle = tempfile.NamedTemporaryFile(
        prefix=f"{workbook_path.stem}_",
        suffix=".ods",
        dir=str(workbook_path.parent),
        delete=False,
    )
    temp_handle.close()
    temp_path = Path(temp_handle.name)

    try:
        with zipfile.ZipFile(temp_path, "w") as target_zip:
            for info in source_zip.infolist():
                data = updated_content if info.filename == "content.xml" else source_zip.read(info.filename)
                target_zip.writestr(clone_zip_info(info), data)
        os.replace(temp_path, workbook_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def clone_zip_info(info: zipfile.ZipInfo) -> zipfile.ZipInfo:
    cloned = zipfile.ZipInfo(filename=info.filename, date_time=info.date_time)
    cloned.compress_type = info.compress_type
    cloned.comment = info.comment
    cloned.extra = info.extra
    cloned.create_system = info.create_system
    cloned.create_version = info.create_version
    cloned.extract_version = info.extract_version
    cloned.flag_bits = info.flag_bits
    cloned.volume = info.volume
    cloned.internal_attr = info.internal_attr
    cloned.external_attr = info.external_attr
    return cloned


def qname(prefix: str, name: str) -> str:
    return f"{{{NS[prefix]}}}{name}"


if __name__ == "__main__":
    raise SystemExit(main())

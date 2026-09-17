"""Project EPA DQPL rows as source observations; never match a product or assess it."""

import hashlib
import io
import zipfile
import xml.etree.ElementTree as ET

NS = {
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/package/2006/relationships",
}
SHEET_NAME = "Disqualified Products List"
HEADERS = {
    "B": "Product Type",
    "C": "Organization Name",
    "D": "Brand Name",
    "E": "Product Model Number",
    "F": "Date Disqualified",
}


def _cell_column(reference: str) -> str:
    return "".join(char for char in reference if char.isalpha())


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(item.itertext()) for item in root.findall("x:si", NS)]


def _sheet_xml(archive: zipfile.ZipFile) -> tuple[ET.Element, bool]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    sheet = next(
        (
            item
            for item in workbook.findall("x:sheets/x:sheet", NS)
            if item.get("name") == SHEET_NAME
        ),
        None,
    )
    if sheet is None:
        raise ValueError("EPA DQPL sheet identity invalid")
    rel_id = sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relation = next(
        (item for item in rels.findall("p:Relationship", NS) if item.get("Id") == rel_id), None
    )
    if relation is None or not relation.get("Target", "").startswith("worksheets/"):
        raise ValueError("EPA DQPL sheet relationship invalid")
    properties = workbook.find("x:workbookPr", NS)
    return ET.fromstring(archive.read("xl/" + relation.get("Target"))), (
        properties is not None and properties.get("date1904") == "1"
    )


def _row_cells(row: ET.Element, strings: list[str]) -> dict[str, dict]:
    result = {}
    for cell in row.findall("x:c", NS):
        reference = cell.get("r", "")
        value = cell.find("x:v", NS)
        inline = cell.find("x:is", NS)
        if value is None and inline is None:
            continue
        raw = "".join(inline.itertext()) if inline is not None else value.text
        cell_type = cell.get("t")
        if cell_type == "s":
            raw = strings[int(raw)]
        result[_cell_column(reference)] = {
            "cell": reference,
            "value_raw": raw,
            "type_raw": cell_type,
            "style_raw": cell.get("s"),
        }
    return result


def observe_rows(body: bytes, *, source_body_sha256: str, captured_at: str) -> dict:
    """Validate exact source layout and return raw row observations only."""
    if hashlib.sha256(body).hexdigest() != source_body_sha256:
        raise ValueError("EPA DQPL body hash provenance invalid")
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        sheet, date1904 = _sheet_xml(archive)
        strings = _shared_strings(archive)
    rows = {
        _row.get("r"): _row_cells(_row, strings) for _row in sheet.findall("x:sheetData/x:row", NS)
    }
    header = rows.get("5", {})
    if {column: header.get(column, {}).get("value_raw") for column in HEADERS} != HEADERS:
        raise ValueError("EPA DQPL headers changed")
    interval = rows.get("3", {}).get("B", {}).get("value_raw")
    if not interval:
        raise ValueError("EPA DQPL stated interval missing")
    observations = []
    for number, cells in rows.items():
        if int(number) < 6 or not cells:
            continue
        if set(cells) != set(HEADERS):
            raise ValueError("EPA DQPL data row has missing or unexpected columns")
        observations.append(
            {
                "source_body_sha256": source_body_sha256,
                "captured_at": captured_at,
                "sheet_name": SHEET_NAME,
                "source_interval_raw": interval,
                "source_row": int(number),
                "workbook_date1904": date1904,
                "cells": {name: cells[column] for column, name in HEADERS.items()},
                "identity_matching": "NOT_EVALUATED",
                "disqualification_state": "NOT_EVALUATED",
                "assessment": "NOT_EVALUATED",
            }
        )
    if not observations:
        raise ValueError("EPA DQPL has no value-bearing data rows")
    return {
        "contract": "G2_EPA_DQPL_ROW_OBSERVATION_ONLY_V1",
        "source_body_sha256": source_body_sha256,
        "observation_count": len(observations),
        "observations": observations,
    }

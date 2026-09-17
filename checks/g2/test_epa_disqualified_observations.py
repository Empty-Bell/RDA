import hashlib
import io
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_epa_disqualified_observations import observe_rows  # noqa: E402


def workbook(*, model="00106", header="Product Model Number", missing=False):
    workbook_xml = '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Disqualified Products List" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>'
    values = [
        ("B3", "1/1/2018 to 5/15/2026"),
        ("B5", "Product Type"),
        ("C5", "Organization Name"),
        ("D5", "Brand Name"),
        ("E5", header),
        ("F5", "Date Disqualified"),
        ("B6", "Refrigerators and Freezers"),
        ("C6", "Org"),
        ("D6", "Brand"),
        ("E6", model),
        ("F6", "44000"),
    ]
    if missing:
        values = [item for item in values if item[0] != "F6"]
    sheet = (
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="3"><c r="B3" t="inlineStr"><is><t>1/1/2018 to 5/15/2026</t></is></c></row><row r="5">'
        + "".join(
            f'<c r="{ref}" t="inlineStr"><is><t>{value}</t></is></c>'
            for ref, value in values
            if ref.endswith("5")
        )
        + '</row><row r="6">'
        + "".join(
            f'<c r="{ref}" t="inlineStr"><is><t>{value}</t></is></c>'
            for ref, value in values
            if ref.endswith("6")
        )
        + "</row></sheetData></worksheet>"
    )
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return raw.getvalue()


class DqplObservationTests(unittest.TestCase):
    def test_preserves_raw_identifier_and_provenance_without_matching(self):
        body = workbook(model="00106")
        result = observe_rows(
            body,
            source_body_sha256=hashlib.sha256(body).hexdigest(),
            captured_at="2026-09-17T00:00:00Z",
        )
        row = result["observations"][0]
        self.assertEqual(result["observation_count"], 1)
        self.assertEqual(row["cells"]["Product Model Number"]["value_raw"], "00106")
        self.assertEqual(row["identity_matching"], "NOT_EVALUATED")
        self.assertEqual(row["source_row"], 6)

    def test_rejects_changed_hash_headers_and_incomplete_rows(self):
        body = workbook()
        with self.assertRaisesRegex(ValueError, "hash"):
            observe_rows(body, source_body_sha256="0" * 64, captured_at="x")
        for candidate in (workbook(header="Changed"), workbook(missing=True)):
            with self.assertRaises(ValueError):
                observe_rows(
                    candidate,
                    source_body_sha256=hashlib.sha256(candidate).hexdigest(),
                    captured_at="x",
                )

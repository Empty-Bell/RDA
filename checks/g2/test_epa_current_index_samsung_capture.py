import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_epa_current_index_samsung_capture import (  # noqa: E402
    metadata_projection,
    page_query_params,
    page_rows,
    replay_capture,
    scan_projection,
)


def metadata() -> dict:
    return {
        "id": "8wj2-sec8",
        "rowsUpdatedAt": 1,
        "viewLastModified": 2,
        "columns": [
            {"fieldName": value}
            for value in ("pd_id", "brand_name", "model_number", "energy_star_model_identifier")
        ],
    }


def row(number: str, source_id: str) -> dict:
    return {
        "source_row_id": source_id,
        "pd_id": "pd-" + source_id,
        "brand_name": "Samsung",
        "model_number": number,
        "energy_star_model_identifier": "cb-" + source_id,
    }


class SamsungScopeTests(unittest.TestCase):
    def test_page_query_uses_socrata_select_order(self):
        self.assertEqual(page_query_params(0)["$select"], "*,:id as source_row_id")
        with self.assertRaisesRegex(ValueError, "offset"):
            page_query_params(1)

    def test_complete_scan_preserves_duplicate_candidate_keys(self):
        before = metadata_projection(json.dumps(metadata()).encode())
        pages = [
            [
                row("MODEL", "1"),
                {
                    **row("MODEL", "2"),
                    "pd_id": "pd-1",
                    "energy_star_model_identifier": "cb-1",
                },
            ]
        ]
        scan = scan_projection(pages, 2, 2, before, before)
        self.assertEqual(scan["query_completeness"], "COMPLETE_OBSERVED_QUERY")
        self.assertEqual(scan["duplicate_candidate_key_count"], 1)

    def test_non_samsung_and_changed_metadata_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-Samsung"):
            page_rows(json.dumps([{**row("MODEL", "1"), "brand_name": "Other"}]).encode())
        before = metadata_projection(json.dumps(metadata()).encode())
        changed = metadata_projection(json.dumps({**metadata(), "rowsUpdatedAt": 3}).encode())
        with self.assertRaisesRegex(ValueError, "changed"):
            scan_projection([[row("MODEL", "1")]], 1, 1, before, changed)

    def test_replay_rejects_tampered_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            values = {
                "metadata-before": metadata(),
                "count-before": [{"row_count": "1"}],
                "page-0000": [row("MODEL", "1")],
                "count-after": [{"row_count": "1"}],
                "metadata-after": metadata(),
            }
            records = []
            for name, value in values.items():
                body = json.dumps(value).encode()
                filename = name + ".bin"
                (root / filename).write_bytes(body)
                records.append(
                    {
                        "name": name,
                        "file": filename,
                        "url": "https://example.test/" + name,
                        "status": 200,
                        "content_type": "application/json",
                        "body_sha256": hashlib.sha256(body).hexdigest(),
                        "size_bytes": len(body),
                    }
                )
            before = metadata_projection(json.dumps(metadata()).encode())
            manifest = {
                "sources": records,
                "metadata_before": before,
                "metadata_after": before,
                "scan": scan_projection([[row("MODEL", "1")]], 1, 1, before, before),
            }
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(replay_capture(root), manifest)
            (root / "page-0000.bin").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash"):
                replay_capture(root)


if __name__ == "__main__":
    unittest.main()

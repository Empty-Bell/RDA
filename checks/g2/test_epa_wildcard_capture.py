import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_epa_wildcard_capture import (  # noqa: E402
    positional_diagnostic,
    project_source,
    replay_capture,
    source_record,
)


class EpaWildcardCaptureTests(unittest.TestCase):
    def test_positional_diagnostic_is_provenance_bound_and_non_identity(self):
        kwargs = {"dataset_id": "p5st-her9", "metadata_sha256": "a" * 64}
        self.assertEqual(
            positional_diagnostic("RF23D*9600**", "RF23DB9600QL", **kwargs)["diagnostic"],
            "POSITIONAL_COMPATIBLE_DIAGNOSTIC_ONLY",
        )
        self.assertEqual(
            positional_diagnostic("RF23D*9600**", "RF23DB9600QLAA", **kwargs)["diagnostic"],
            "WITHHELD_LENGTH_MISMATCH",
        )
        self.assertEqual(
            positional_diagnostic("RF23D*9600**", "RF23D89600QL", **kwargs)["diagnostic"],
            "POSITIONAL_INCOMPATIBLE_DIAGNOSTIC_ONLY",
        )
        self.assertEqual(
            positional_diagnostic("ABC##", "ABC/01", **kwargs)["diagnostic"],
            "WITHHELD_UNSUPPORTED_SYNTAX",
        )
        self.assertEqual(
            positional_diagnostic("ABC##", "ABC01", **kwargs)["identity_state"], "NOT_EVALUATED"
        )

    def test_html_shell_does_not_establish_product_observation(self):
        self.assertEqual(
            project_source("refrigerator-record-2839420", b"<div id='main'></div>")[
                "content_status"
            ],
            "SHELL_OR_PRODUCT_TEXT_NOT_OBSERVED",
        )

    def test_api_projection_preserves_upc_and_rejects_ambiguous_records(self):
        row = {
            "pd_id": "2839420",
            "brand_name": "Samsung",
            "model_number": "RF23D*9600**",
            "upc": "00123",
            "markets": "United States, Canada",
        }
        self.assertEqual(
            project_source("refrigerator-api-record", json.dumps([row]).encode())["upc"], "00123"
        )
        for rows in ([], [row, row], [{**row, "pd_id": "other"}]):
            with self.assertRaises(ValueError):
                project_source("refrigerator-api-record", json.dumps(rows).encode())

    def test_malformed_metadata_is_not_identity_evidence(self):
        for data in ({}, {"id": "p5st-her9", "columns": []}, {"id": "other", "columns": []}):
            with self.assertRaises(ValueError):
                project_source("refrigerator-metadata", json.dumps(data).encode())

    def test_source_record_rejects_failed_or_empty_response(self):
        with self.assertRaises(ValueError):
            source_record("x", "https://example.com", 403, "text/html", b"no")
        with self.assertRaises(ValueError):
            source_record("x", "https://example.com", 200, "text/html", b"")

    def test_replay_requires_exact_preserved_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = b"official source"
            (root / "x.bin").write_bytes(raw)
            (root / "manifest.json").write_text(
                json.dumps(
                    {"sources": [{"name": "x", "body_sha256": hashlib.sha256(raw).hexdigest()}]}
                ),
                encoding="utf-8",
            )
            self.assertEqual(replay_capture(root)["sources"][0]["name"], "x")
            (root / "x.bin").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash"):
                replay_capture(root)

    def test_replay_rejects_projection_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = b"official source"
            record = {
                "name": "x",
                "body_sha256": hashlib.sha256(raw).hexdigest(),
                "projection": {"value": "source"},
            }
            (root / "x.bin").write_bytes(raw)
            (root / "manifest.json").write_text(json.dumps({"sources": [record]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                replay_capture(root)

import json
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_epa_current_index_capture import (  # noqa: E402
    project,
    replay_capture,
    validate_cross_source,
)


class CurrentIndexTests(unittest.TestCase):
    def test_projects_and_cross_checks_exact_keys(self):
        row = {
            "pd_id": "2839420",
            "brand_name": "Samsung",
            "model_number": "RF23D*9600**",
            "energy_star_model_identifier": "CB",
            "markets": "United States",
        }
        index = project("model-index-row", json.dumps([row]).encode())
        refrigerator = project("refrigerator-row", json.dumps([row]).encode())
        self.assertEqual(
            validate_cross_source(index, refrigerator)["cross_source_key_agreement"], "OBSERVED"
        )

    def test_missing_duplicate_and_disagreement_are_rejected(self):
        row = {
            "pd_id": "2839420",
            "brand_name": "Samsung",
            "model_number": "RF23D*9600**",
            "energy_star_model_identifier": "CB",
        }
        for value in ([], [row, row], [{**row, "pd_id": "1"}]):
            with self.assertRaises(ValueError):
                project("model-index-row", json.dumps(value).encode())
        with self.assertRaises(ValueError):
            validate_cross_source(row, {**row, "model_number": "OTHER"})

    def test_metadata_requires_current_index_identity_and_fields(self):
        good = {
            "id": "8wj2-sec8",
            "columns": [
                {"fieldName": x}
                for x in ("pd_id", "brand_name", "model_number", "energy_star_model_identifier")
            ],
        }
        self.assertEqual(
            project("model-index-metadata", json.dumps(good).encode())["id"], "8wj2-sec8"
        )
        with self.assertRaises(ValueError):
            project("model-index-metadata", json.dumps({"id": "other", "columns": []}).encode())

    def test_replay_rejects_changed_bytes(self):
        row = {
            "pd_id": "2839420",
            "brand_name": "Samsung",
            "model_number": "RF23D*9600**",
            "energy_star_model_identifier": "CB",
        }
        metadata = {
            "id": "8wj2-sec8",
            "columns": [
                {"fieldName": value}
                for value in ("pd_id", "brand_name", "model_number", "energy_star_model_identifier")
            ],
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sources = []
            projections = {}
            for name, data in (
                ("model-index-metadata", metadata),
                ("model-index-row", row),
                ("refrigerator-row", row),
            ):
                body = json.dumps(data if name.endswith("metadata") else [data]).encode()
                (root / (name + ".bin")).write_bytes(body)
                sources.append({"name": name, "body_sha256": hashlib.sha256(body).hexdigest()})
                projections[name] = project(name, body)
            manifest = {
                "sources": sources,
                "projections": projections,
                "cross_source": validate_cross_source(
                    projections["model-index-row"], projections["refrigerator-row"]
                ),
            }
            (root / "manifest.json").write_text(json.dumps(manifest))
            self.assertEqual(replay_capture(root), manifest)
            (root / "model-index-row.bin").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash"):
                replay_capture(root)

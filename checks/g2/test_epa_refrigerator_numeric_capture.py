import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from g2_epa_refrigerator_numeric_capture import (  # noqa: E402
    build_projection,
    candidate_ids,
    load_binding,
    replay_capture,
)


def record(sku, candidates):
    return {
        "exact_sku": {"exact_sku_raw": sku},
        "raw_literal_candidates": [],
        "approved_normalized_literal_candidates": [],
        "current_index_pattern_candidates": [
            {"pd_id": value} for value in candidates
        ],
    }


class EpaRefrigeratorNumericCaptureTests(unittest.TestCase):
    def test_consolidates_equal_multi_candidate_values_and_preserves_no_candidate(self):
        binding = {
            "contract": "G2_SAME_RUN_ENERGY_STAR_DECLARATION_CURRENT_INDEX_BINDING_V2",
            "source_run_id": "run-1",
            "scan_query_completeness": "COMPLETE_OBSERVED_QUERY",
            "records": [record("SKU-A", ["10", "11"]), record("SKU-B", [])],
        }
        rows = [
            {"pd_id": "10", "annual_energy_use_kwh_yr": "600", "capacity_total_volume_ft3": "22.5"},
            {"pd_id": "11", "annual_energy_use_kwh_yr": "600", "capacity_total_volume_ft3": "22.5"},
        ]
        result = build_projection(binding, rows)
        self.assertEqual(result["records"][0]["annual_energy_kwh"]["amount"], 600.0)
        self.assertEqual(result["records"][0]["capacity_cu_ft"]["state"], "VALUE")
        self.assertEqual(result["records"][1]["annual_energy_kwh"]["state"], "NO_CURRENT_INDEX_CANDIDATE")
        self.assertFalse(result["scope"]["changes_certification_assessment"])
        self.assertFalse(result["assessment_enabled"])

    def test_withholds_conflicting_or_partial_candidate_values(self):
        binding = {"source_run_id": "run-1", "records": [record("SKU-A", ["10", "11"])]}
        conflict = build_projection(binding, [
            {"pd_id": "10", "annual_energy_use_kwh_yr": "600", "capacity_total_volume_ft3": "22.5"},
            {"pd_id": "11", "annual_energy_use_kwh_yr": "601", "capacity_total_volume_ft3": "22.5"},
        ])
        self.assertEqual(conflict["records"][0]["annual_energy_kwh"]["state"], "CONFLICTING_EPA_VALUES")
        partial = build_projection(binding, [
            {"pd_id": "10", "annual_energy_use_kwh_yr": "600", "capacity_total_volume_ft3": "22.5"},
        ])
        self.assertEqual(partial["records"][0]["capacity_cu_ft"]["state"], "PARTIAL_EPA_FAMILY_COVERAGE")

    def test_loads_only_complete_v2_binding(self):
        binding = {
            "contract": "G2_SAME_RUN_ENERGY_STAR_DECLARATION_CURRENT_INDEX_BINDING_V2",
            "scan_query_completeness": "COMPLETE_OBSERVED_QUERY",
            "records": [],
        }
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "source.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("g2/run/energy-star-source/current-index-binding.json", json.dumps(binding))
            self.assertEqual(load_binding(archive), binding)
        self.assertEqual(candidate_ids(record("SKU", ["2", "1", "2"])), ["1", "2"])

    def test_replay_rejects_tampered_raw_source(self):
        binding = {
            "contract": "G2_SAME_RUN_ENERGY_STAR_DECLARATION_CURRENT_INDEX_BINDING_V2",
            "source_run_id": "run-1", "scan_query_completeness": "COMPLETE_OBSERVED_QUERY",
            "records": [record("SKU-A", ["10"])],
        }
        rows = [{"pd_id": "10", "brand_name": "Samsung", "model_number": "SKU-A",
                 "annual_energy_use_kwh_yr": "600", "capacity_total_volume_ft3": "22.5"}]
        metadata = {"id": "p5st-her9", "rowsUpdatedAt": 1, "viewLastModified": 2,
                    "columns": [{"fieldName": value} for value in (
                        "pd_id", "brand_name", "model_number", "annual_energy_use_kwh_yr",
                        "capacity_total_volume_ft3") ]}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "source.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("g2/run/energy-star-source/current-index-binding.json", json.dumps(binding))
            bodies = {"metadata-before": json.dumps(metadata).encode(), "rows": json.dumps(rows).encode(),
                      "metadata-after": json.dumps(metadata).encode()}
            sources = []
            import hashlib
            for name, body in bodies.items():
                filename = name + ".json"
                (root / filename).write_bytes(body)
                sources.append({"name": name, "file": filename, "body_sha256": hashlib.sha256(body).hexdigest()})
            projection = build_projection(binding, rows)
            projection.update({"sources": sources, "metadata": {
                "id": "p5st-her9", "rows_updated_at": 1, "view_last_modified": 2,
                "fields": sorted(metadata_column["fieldName"] for metadata_column in metadata["columns"]),
            }})
            (root / "projection.json").write_text(json.dumps(projection), encoding="utf-8")
            self.assertEqual(replay_capture(archive, root)["status"], "PASS")
            (root / "rows.json").write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                replay_capture(archive, root)


if __name__ == "__main__":
    unittest.main()

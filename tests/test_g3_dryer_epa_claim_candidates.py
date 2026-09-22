import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.g3_dryer_epa_claim_candidates import build_report, positional_candidate


class DryerEpaClaimCandidateContract(unittest.TestCase):
    def test_positional_star_is_candidate_only_and_suffix_is_retained(self):
        candidate = positional_candidate("DV90F8**", "DV90F8AB1")
        self.assertEqual(candidate["candidate_basis"],
                         "POSITIONAL_PREFIX_PATTERN; EACH * = ONE A-Z/0-9 CHARACTER")
        self.assertEqual(candidate["matched_prefix_raw"], "DV90F8AB")
        self.assertEqual(candidate["remaining_sku_suffix_raw"], "1")

    def test_literal_model_does_not_expand_as_prefix(self):
        self.assertIsNone(positional_candidate("DV90F8", "DV90F8AB1"))
        self.assertIsNotNone(positional_candidate("DV90F8", "DV90F8"))

    def test_claims_and_epa_rows_join_without_numeric_assessment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            collection = root / "collection"
            (collection / "pdp" / "DV90F8AB1").mkdir(parents=True)
            (collection / "collection-summary.json").write_text(json.dumps({
                "status": "PASS", "contract": "G3_DRYER_EXACT_SKU_PDP_V1",
                "collection_run_id": "101", "coverage": {"population_count": 1}}))
            (collection / "products.json").write_text(json.dumps([{"exact_sku": "DV90F8AB1"}]))
            claims = {"exact_sku": "DV90F8AB1", "plp_energy_star_flag_raw": "Y",
                      "pdp_spec_energy_star_claim_raw": [{"name": "ENERGY STAR", "value": "Yes"}],
                      "rendered_attributed_badges_raw": []}
            snapshot = {"target_sku": "DV90F8AB1",
                        "primary_logo_inspection": "SUPPORTED_PRIMARY_SURFACE_COMPLETE",
                        "spec_surface_inspection": "SUPPORTED_VISIBLE_SPEC_TABLE_COMPLETE",
                        "visible_spec_energy_star_rows": [{"text": "ENERGY STAR Certification Yes"}]}
            snapshot_raw = json.dumps(snapshot).encode()
            (collection / "pdp" / "DV90F8AB1" / "snapshot.json").write_bytes(snapshot_raw)
            (collection / "pdp" / "DV90F8AB1" / "result.json").write_text(json.dumps({
                "exact_sku": "DV90F8AB1", "status": "VERIFIED_EXACT_IDENTITY",
                "snapshot_sha256": hashlib.sha256(snapshot_raw).hexdigest(),
                "energy_star_claim_sources_raw": claims}))

            epa_dir = root / "epa"
            combo_dir = root / "combo"
            epa_dir.mkdir()
            combo_dir.mkdir()
            epa_rows = [{"source_row_id": "epa-row-1", "pd_id": "1001",
                         "model_number": "DV90F8**", "markets": "US", "date_qualified": "2026-01-01",
                         "annual_energy_use_kwh_yr": "999"}]
            combo_rows = [{"source_row_id": "combo-row-1", "pd_id": "1002",
                           "model_number": "DV90F8**", "markets": "US", "date_qualified": "2026-01-02",
                           "annual_energy_use_kwh_year": "111", "special_type": "Combo"}]
            for path, dataset, run_id, rows in (
                (epa_dir, "t9u7-4d2j", "202", epa_rows),
                (combo_dir, "9jai-gs6t", "202", combo_rows),
            ):
                raw = json.dumps(rows).encode()
                (path / "samsung-current-rows.json").write_bytes(raw)
                (path / "capture-summary.json").write_text(json.dumps({
                    "status": "PASS", "dataset_id": dataset, "capture_run_id": run_id,
                    "row_count": len(rows), "rows_sha256": hashlib.sha256(raw).hexdigest()}))

            report = build_report(collection, "101", epa_dir, "202", combo_dir, "202", root / "out")
            row = report["rows"][0]
            self.assertEqual(report["status"], "SOURCE_CANDIDATES_READY")
            self.assertEqual(report["source_validation"], "PASS")
            self.assertEqual(row["energy_star_claim_sources_raw"]["plp_energy_star_flag_raw"], "Y")
            self.assertEqual(row["energy_star_claim_sources_raw"]["pdp_logo_inspection_raw"],
                             "SUPPORTED_PRIMARY_SURFACE_COMPLETE")
            self.assertEqual(row["energy_star_claim_sources_raw"]["pdp_visible_spec_energy_star_rows_raw"],
                             snapshot["visible_spec_energy_star_rows"])
            self.assertEqual(len(row["dryer_epa_model_pattern_candidates"]), 1)
            self.assertEqual(len(row["combo_epa_model_pattern_candidates"]), 1)
            self.assertEqual(row["assessment"], "NOT_EVALUATED")
            def keys(value):
                if isinstance(value, dict):
                    return [key.lower() for key in value] + [key for item in value.values() for key in keys(item)]
                if isinstance(value, list):
                    return [key for item in value for key in keys(item)]
                return []
            report_keys = keys(report)
            self.assertFalse(any("annual_energy" in key or "energyguide" in key for key in report_keys))

    def test_epa_capture_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, dataset in (("dryer", "t9u7-4d2j"), ("combo", "9jai-gs6t")):
                (root / name).mkdir()
            epa = root / "dryer"
            (epa / "samsung-current-rows.json").write_text("[]")
            (epa / "capture-summary.json").write_text(json.dumps({
                "status": "PASS", "dataset_id": "t9u7-4d2j", "capture_run_id": "202",
                "row_count": 0, "rows_sha256": "wrong"}))
            with self.assertRaisesRegex(ValueError, "identity/hash"):
                from scripts.g3_dryer_epa_claim_candidates import load_epa
                load_epa(epa, "202", "dryer")

    def test_hosted_workflow_contains_only_epa_claim_candidate_steps(self):
        workflow = (Path(__file__).parents[1] / ".github/workflows/g3-dryer-secondary-sources.yml").read_text()
        self.assertIn("g3_dryer_epa_capture.py", workflow)
        self.assertIn("g3_dryer_combo_epa_capture.py", workflow)
        self.assertIn("g3_dryer_epa_claim_candidates.py", workflow)
        self.assertIn("g3_dryer_energy_star_assessment.py", workflow)
        self.assertIn("workflows: [G3 clothes dryer exact-SKU collection]", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertNotIn("EnergyGuide", workflow)
        self.assertNotIn("energyguide", workflow.lower())
        collection_workflow = (Path(__file__).parents[1] / ".github/workflows/g3-dryer-collection.yml").read_text()
        self.assertIn("workflows: [G3 clothes dryer source reconnaissance]", collection_workflow)
        self.assertNotIn("\n  push:", collection_workflow)


if __name__ == "__main__":
    unittest.main()

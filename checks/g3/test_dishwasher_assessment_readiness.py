import json
import tempfile
import unittest
from pathlib import Path

from scripts.g3_dishwasher_assessment import build,readiness


class DishwasherReadinessTests(unittest.TestCase):
    def sources(self):
        energy = {"status": "PASS", "source_bundle_fingerprint": "sha256:bundle-1", "records": [
            {"exact_sku": "SKU-A", "outcome": "PASS"}]}
        numeric = {"status": "PASS", "source_bundle_fingerprint": "sha256:bundle-1", "source_package_sha256": "a" * 64, "rows": [
            {"exact_sku": "SKU-A", "energyguide_annual_energy": {"state": "VALUE", "value": "225"},
             "pdp_annual_energy": {"state": "VALUE", "value": "225"},
             "pdp_vs_energyguide_energy": "EQUAL"}]}
        model = {"status": "PASS", "source_bundle_fingerprint": "sha256:bundle-1", "source_package_sha256": "a" * 64, "records": [
            {"exact_sku": "SKU-A", "pdp_vs_energyguide_model": "EQUAL",
             "energyguide_model_pattern_source": "HUMAN_VISUAL_REVIEW"}]}
        return energy, numeric, model

    def test_complete_bound_controls_are_ready(self):
        self.assertEqual(readiness(*self.sources())["status"], "READY_FOR_ASSESSMENT")

    def test_missing_label_energy_never_becomes_pass(self):
        energy, numeric, model = self.sources()
        numeric["rows"][0]["energyguide_annual_energy"] = {"state": "NOT_OBSERVED"}
        numeric["rows"][0]["pdp_vs_energyguide_energy"] = "NOT_COMPARABLE"
        result = readiness(energy, numeric, model)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("US_ENERGYGUIDE_ANNUAL_UNRESOLVED", {gap["code"] for gap in result["gaps"]})

    def test_unreviewed_ocr_mismatch_and_mixed_runs_block(self):
        energy, numeric, model = self.sources()
        model["source_bundle_fingerprint"] = "sha256:bundle-2"
        model["records"][0].update(pdp_vs_energyguide_model="DIFFERENT",
                                   energyguide_model_pattern_source="RAW_OCR")
        codes = {gap["code"] for gap in readiness(energy, numeric, model)["gaps"]}
        self.assertIn("CONTROL_SOURCE_BUNDLE_UNBOUND", codes)
        self.assertIn("RAW_OCR_MODEL_MISMATCH_UNREVIEWED", codes)

    def test_different_comparison_packages_block(self):
        energy, numeric, model = self.sources()
        model["source_package_sha256"] = "b" * 64
        self.assertIn("CONTROL_COMPARISON_PACKAGE_DIFFERS", {gap["code"] for gap in readiness(energy,numeric,model)["gaps"]})

    def test_old_model_comparison_with_matching_fixed_prefix_stays_blocked(self):
        energy,numeric,model=self.sources()
        model["records"][0].update(normalized_pdp_model="DW80CG5450SR",pdp_vs_energyguide_model="DIFFERENT",energyguide_model_patterns_visual_reviewed=["DW80CG54******"])
        self.assertIn("MODEL_PREFIX_COMPARISON_STALE",{gap["code"] for gap in readiness(energy,numeric,model)["gaps"]})

    def test_missing_pdp_gets_low_only_with_label_epa_agreement(self):
        energy,numeric,model=self.sources()
        numeric["rows"][0].update(pdp_annual_energy={"state":"NOT_OBSERVED"},energyguide_vs_epa_energy="NOT_COMPARABLE")
        model["records"][0].update(pdp_vs_epa_model="EQUAL",energyguide_vs_epa_model="EQUAL")
        with tempfile.TemporaryDirectory() as temp:
            paths=[Path(temp)/name for name in ("energy.json","numeric.json","model.json")]
            for path,data in zip(paths,(energy,numeric,model)): path.write_text(json.dumps(data))
            build(*paths,Path(temp)/"out")
            report=json.loads((Path(temp)/"out"/"assessment.json").read_text())
        self.assertEqual(report["counts"]["PASS"],1)
        self.assertEqual(report["finding_count"],0)


if __name__ == "__main__":
    unittest.main()

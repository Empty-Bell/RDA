import unittest

from scripts.g3_dishwasher_assessment import readiness


class DishwasherReadinessTests(unittest.TestCase):
    def sources(self):
        energy = {"status": "PASS", "source_run_id": "run-1", "records": [
            {"exact_sku": "SKU-A", "outcome": "PASS"}]}
        numeric = {"status": "PASS", "source_run_id": "run-1", "rows": [
            {"exact_sku": "SKU-A", "energyguide_annual_energy": {"state": "VALUE", "value": "225"},
             "pdp_annual_energy": {"state": "VALUE", "value": "225"},
             "pdp_vs_energyguide_energy": "EQUAL"}]}
        model = {"status": "PASS", "source_run_id": "run-1", "records": [
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
        model["source_run_id"] = "run-2"
        model["records"][0].update(pdp_vs_energyguide_model="DIFFERENT",
                                   energyguide_model_pattern_source="RAW_OCR")
        codes = {gap["code"] for gap in readiness(energy, numeric, model)["gaps"]}
        self.assertIn("CONTROL_SOURCE_RUN_UNBOUND", codes)
        self.assertIn("RAW_OCR_MODEL_MISMATCH_UNREVIEWED", codes)


if __name__ == "__main__":
    unittest.main()

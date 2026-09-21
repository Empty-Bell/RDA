import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from g2_energyguide_numeric_comparison import build_comparison, render_markdown  # noqa: E402


def observation(value=None, state="VALUE"):
    return {"state": state, "value": value if state == "VALUE" else None, "error": None}


class EnergyGuideNumericComparisonTests(unittest.TestCase):
    def test_records_differences_without_issuing_findings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "source.zip"
            replay_path = root / "replay.json"
            products = [{"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}]
            facts = [
                {"kind": "PDP", "exact_sku": "SKU-A", "observations": {
                    "pdp_annual_energy_kwh": observation({"amount": 700, "unit": "kWh/year"}),
                    "pdp_capacity": observation({"amount": 29, "unit": "cu ft"}),
                }},
                {"kind": "PDP", "exact_sku": "SKU-B", "observations": {
                    "pdp_annual_energy_kwh": observation(state="NOT_OBSERVED"),
                    "pdp_capacity": observation({"amount": 22.8, "unit": "cu ft"}),
                }},
            ]
            bundle = {"manifest": {"run_id": "run-1", "git_sha": "a" * 40}, "products": products, "facts": facts}
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("g2/run/bundle.json", json.dumps(bundle))
            replay = {
                "contract": "G2_LABEL_ANNOTATION_REPLAY_V1", "status": "PASS",
                "source": {"execution_run_id": "run-1"},
                "label_selection_summary": {"records": [
                    {"exact_sku": "SKU-A", "annual_energy_observation": observation({"amount": 700, "unit": "kWh/year"})},
                    {"exact_sku": "SKU-B", "annual_energy_observation": observation({"amount": 600, "unit": "kWh/year"})},
                ]},
                "capacity_selection_summary": {"records": [
                    {"exact_sku": "SKU-A", "capacity_observation": observation({"amount": 28.6, "unit": "Cubic Feet"})},
                    {"exact_sku": "SKU-B", "capacity_observation": observation({"amount": 22.8, "unit": "Cubic Feet"})},
                ]},
            }
            replay_path.write_text(json.dumps(replay), encoding="utf-8")
            result = build_comparison(archive, replay_path)
            self.assertEqual(result["counts"]["annual_energy"], {"EQUAL": 1, "DIFFERENT": 0, "NOT_COMPARABLE": 1})
            self.assertEqual(result["counts"]["capacity"], {"EQUAL": 1, "DIFFERENT": 1, "NOT_COMPARABLE": 0})
            self.assertEqual(result["records"][0]["capacity_cu_ft"]["delta_pdp_minus_label"], 0.4)
            self.assertFalse(result["assessment_enabled"])
            self.assertEqual(result["overall_product_compliance"], "NOT_EVALUATED")
            self.assertIn("does not apply a tolerance", render_markdown(result))


if __name__ == "__main__":
    unittest.main()

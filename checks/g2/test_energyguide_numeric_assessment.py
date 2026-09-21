from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from g2_energyguide_numeric_assessment import build_assessment, render_markdown  # noqa: E402


def measurement(state, reason, pdp, label, epa):
    return {
        "state": state, "reason": reason, "pdp_amount": pdp, "label_amount": label,
        "epa_amount": epa, "epa_state": "VALUE" if epa is not None else "NO_CURRENT_INDEX_CANDIDATE",
        "label_epa_relation": "EQUAL" if label == epa else "NOT_COMPARABLE",
        "pdp_epa_relation": "EQUAL" if pdp == epa else "DIFFERENT" if pdp is not None and epa is not None else "NOT_COMPARABLE",
        "delta_pdp_minus_label": None if pdp is None or label is None else pdp - label,
    }


class EnergyGuideNumericAssessmentTests(unittest.TestCase):
    def comparison(self):
        return {
            "contract": "G2_ENERGYGUIDE_PDP_NUMERIC_COMPARISON_OBSERVATION_V1",
            "status": "PASS", "assessment_enabled": False,
            "source": {"execution_run_id": "run-1"},
            "scope": {"comparison_mode": "OBSERVATION_ONLY_NO_TOLERANCE_NO_FINDINGS"},
            "records": [
                {"exact_sku": "SKU-A",
                 "annual_energy_kwh": measurement("NOT_COMPARABLE", "PDP_VALUE_MISSING", None, 600, 600),
                 "capacity_cu_ft": measurement("DIFFERENT", "OBSERVED_NUMERIC_DIFFERENCE", 23.0, 22.6, 22.6)},
                {"exact_sku": "SKU-B",
                 "annual_energy_kwh": measurement("EQUAL", "EXACT_NUMERIC_EQUALITY", 700, 700, 700),
                 "capacity_cu_ft": measurement("EQUAL", "EXACT_NUMERIC_EQUALITY", 28.6, 28.6, 28.6)},
                {"exact_sku": "SKU-C",
                 "annual_energy_kwh": measurement("NOT_COMPARABLE", "PDP_VALUE_MISSING", None, 500, None),
                 "capacity_cu_ft": measurement("NOT_COMPARABLE", "PDP_VALUE_MISSING", None, 20.0, None)},
            ],
        }

    def test_preserves_independent_findings_and_displays_highest_severity(self):
        result = build_assessment(self.comparison())
        self.assertEqual(result["counts"]["finding_count"], 3)
        self.assertEqual(result["counts"]["affected_sku_count"], 2)
        self.assertEqual(result["counts"]["findings_by_severity"], {"MEDIUM": 1, "LOW": 2})
        self.assertEqual(result["counts"]["display"], {"PASS": 1, "MEDIUM": 1, "LOW": 1, "NOT_EVALUATED": 0})
        self.assertEqual(result["records"][0]["display_outcome"], "MEDIUM")
        self.assertEqual(len(result["records"][0]["findings"]), 2)
        self.assertTrue(result["assessment_enabled"])
        self.assertEqual(result["overall_product_compliance"], "NOT_EVALUATED")
        self.assertIn("PDP_ENERGYGUIDE_CAPACITY_MISMATCH", render_markdown(result))

    def test_annual_numeric_difference_is_not_silently_passed(self):
        comparison = self.comparison()
        comparison["records"] = [{
            "exact_sku": "SKU-X",
            "annual_energy_kwh": measurement("DIFFERENT", "OBSERVED_NUMERIC_DIFFERENCE", 600, 601, 601),
            "capacity_cu_ft": measurement("EQUAL", "EXACT_NUMERIC_EQUALITY", 22.5, 22.5, 22.5),
        }]
        result = build_assessment(comparison)
        self.assertEqual(result["records"][0]["display_outcome"], "NOT_EVALUATED")
        self.assertEqual(result["counts"]["finding_count"], 0)

    def test_rejects_duplicate_sku_or_assessed_input(self):
        comparison = self.comparison()
        comparison["records"][1]["exact_sku"] = "SKU-A"
        with self.assertRaisesRegex(ValueError, "duplicated"):
            build_assessment(comparison)
        comparison = self.comparison()
        comparison["assessment_enabled"] = True
        with self.assertRaisesRegex(ValueError, "contract"):
            build_assessment(comparison)


if __name__ == "__main__":
    unittest.main()

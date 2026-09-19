from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_pf_plp_visual_validation import calibrate  # noqa: E402


def card(sku, logos, complete=True):
    return {"sku": sku, "card_scope_contract": "PLP_EXACT_LIST_ITEM_V2", "exact_sku_anchor_count": 1,
            "exact_sku_anchor_values": [sku],
            "logo_inspection": "SUPPORTED_EXACT_CARD_COMPLETE" if complete else "UNSUPPORTED_EXACT_CARD_SCOPE",
            "energy_candidates": logos}


LOGO = {"tag": "IMG", "src": "https://example.test/energy-star-logo.png"}


class PfPlpVisualCalibrationTests(unittest.TestCase):
    def test_y_present_and_n_absent_agree(self):
        report = calibrate(
            [{"exact_sku": "Y", "plp_energy_star_claim_raw": "Y"}, {"exact_sku": "N", "plp_energy_star_claim_raw": "N"}],
            [card("Y", [LOGO]), card("N", [])],
        )
        self.assertEqual(report["calibration_conclusion"], "OBSERVED_AGREEMENT")
        self.assertEqual(report["comparison_counts"]["agreement"], 2)

    def test_visual_mismatch_is_descriptive_not_silenced(self):
        report = calibrate([{"exact_sku": "Y", "plp_energy_star_claim_raw": "Y"}], [card("Y", [])])
        self.assertEqual(report["calibration_conclusion"], "OBSERVED_DISAGREEMENTS")
        self.assertEqual(report["records"][0]["comparison_result"], "DISAGREEMENT")

    def test_unknown_visual_and_unrendered_variant_are_withheld(self):
        report = calibrate(
            [{"exact_sku": "VISIBLE", "plp_energy_star_claim_raw": "Y"}, {"exact_sku": "VARIANT", "plp_energy_star_claim_raw": "N"}],
            [card("VISIBLE", [], complete=False)],
        )
        self.assertEqual(report["comparison_counts"]["comparable"], 0)
        self.assertEqual(report["comparison_counts"]["population_not_rendered"], 1)
        self.assertEqual(report["calibration_conclusion"], "INSUFFICIENT_COMPARABLE_EVIDENCE")

    def test_ambiguous_card_boundary_fails_the_collector(self):
        ambiguous = card("SKU", [LOGO])
        ambiguous["exact_sku_anchor_values"] = ["SKU", "OTHER"]
        ambiguous["exact_sku_anchor_count"] = 2
        with self.assertRaisesRegex(ValueError, "ambiguous exact-SKU ownership"):
            calibrate([{"exact_sku": "SKU", "plp_energy_star_claim_raw": "Y"}], [ambiguous])


if __name__ == "__main__":
    unittest.main()

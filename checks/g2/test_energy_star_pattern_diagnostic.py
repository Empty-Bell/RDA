from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_energy_star_pattern_diagnostic import (  # noqa: E402
    bridge_pattern_candidate,
    compatible_pattern_pairs,
)


REFERENCE = {
    "pd_id": "2839420", "brand_name": "Samsung", "model_number_raw": "RF23D*9600**",
    "energy_star_model_identifier": "CB",
}
BINDING = {
    "contract": "G2_SAME_RUN_ENERGY_STAR_DECLARATION_CURRENT_INDEX_BINDING_V1",
    "source_run_id": "run-1",
    "records": [{"exact_sku": {"exact_sku_raw": "RF23DB9600QLAA", "approved_normalized_identifier": "RF23DB9600QL"},
                 "unresolved_pattern_references": [REFERENCE]}],
}


class EnergyStarPatternDiagnosticTests(unittest.TestCase):
    def test_compatible_pair_requires_normalized_exact_sku(self):
        pairs = compatible_pattern_pairs(BINDING, "a" * 64)
        self.assertEqual(pairs[0]["exact_sku"], "RF23DB9600QLAA")
        without_normalized = {**BINDING, "records": [{**BINDING["records"][0], "exact_sku": {"exact_sku_raw": "RF23DB9600QLAA", "approved_normalized_identifier": None}}]}
        self.assertEqual(compatible_pattern_pairs(without_normalized, "a" * 64), [])

    def test_four_key_bound_candidate_stays_non_assessing(self):
        pair = compatible_pattern_pairs(BINDING, "a" * 64)[0]
        refrigerator_row = {"pd_id": "2839420", "brand_name": "Samsung", "model_number": "RF23D*9600**", "energy_star_model_identifier": "CB"}
        result = bridge_pattern_candidate(pair, refrigerator_row, "a" * 64)
        self.assertEqual(result["pattern_candidate_state"], "PROVENANCE_BOUND_POSITIONAL_CANDIDATE")
        self.assertEqual(result["current_certification_state"], "NOT_EVALUATED")
        self.assertEqual(result["assessment"], "NOT_EVALUATED")

    def test_four_key_mismatch_fails_closed(self):
        pair = compatible_pattern_pairs(BINDING, "a" * 64)[0]
        refrigerator_row = {"pd_id": "2839420", "brand_name": "Samsung", "model_number": "RF23D*9600**", "energy_star_model_identifier": "OTHER"}
        with self.assertRaisesRegex(ValueError, "mismatch"):
            bridge_pattern_candidate(pair, refrigerator_row, "a" * 64)


if __name__ == "__main__":
    unittest.main()

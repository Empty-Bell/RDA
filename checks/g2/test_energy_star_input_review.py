from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_energy_star_input_review import build_input_review  # noqa: E402


DECLARATION = {"exact_sku": "SKU", "plp_energy_star_flag_raw": "Y", "pdp_energy_star_flag_raw": "Y",
               "pdp_energy_star_spec_rows_raw": [{"name": "ENERGY STAR Certified", "value": "Yes"}]}
CANDIDATE = {"exact_sku": {"exact_sku_raw": "SKU"}, "candidate_projection_state": "UNRESOLVED_PATTERN_ENCODINGS_PRESENT",
             "current_certification_state": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"}
BINDING = {"contract": "G2_SAME_RUN_ENERGY_STAR_DECLARATION_CURRENT_INDEX_BINDING_V2", "source_run_id": "run-1",
           "records": [CANDIDATE]}


class EnergyStarInputReviewTests(unittest.TestCase):
    def test_retains_three_source_inputs_and_withholds_assessment(self):
        result = build_input_review([DECLARATION], BINDING)
        record = result["records"][0]
        self.assertEqual(record["plp_logo_source"]["raw_value"], "Y")
        self.assertEqual(record["pdp_spec_certification_source"]["raw_rows"][0]["value"], "Yes")
        self.assertEqual(record["assessment"], "NOT_EVALUATED")

    def test_missing_candidate_sku_fails(self):
        with self.assertRaisesRegex(ValueError, "SKU sets differ"):
            build_input_review([DECLARATION], {**BINDING, "records": []})


if __name__ == "__main__":
    unittest.main()

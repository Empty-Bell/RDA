from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_energy_star_current_index_binding import bind_current_index  # noqa: E402


def row(model):
    return {"source_row_id": "row-1", "pd_id": "123", "brand_name": "SAMSUNG",
            "model_number": model, "energy_star_model_identifier": "ES-1",
            "product_category": "Consumer Refrigeration Products", "product_type": "Refrigerator"}


SOURCE = {"name": "page-0", "body_sha256": "a" * 64}
SCAN = {"source_run_id": "run-1", "query_completeness": "COMPLETE_OBSERVED_QUERY",
        "current_certification_state": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"}
MANIFEST = {"status": "PASS", "run_id": "run-1", "declarations": [
    {"exact_sku": "RF23DB9600QLAA", "source_family_id": "G", "representative_sku": "RF23DB9600QLAA",
     "sku_role": "REPRESENTATIVE", "plp_energy_star_flag_raw": "Y", "pdp_energy_star_flag_raw": "Y",
     "pdp_energy_star_spec_rows_raw": []}
]}


class EnergyStarCurrentIndexBindingTests(unittest.TestCase):
    @patch("g2_energy_star_current_index_binding.load_replayed_rows")
    def test_normalized_literal_candidate_retains_source_declaration(self, mocked):
        mocked.return_value = SCAN, [(row("RF23DB9600QL"), SOURCE)]
        result = bind_current_index(MANIFEST, Path("ignored"))
        record = result["records"][0]
        self.assertEqual(record["candidate_projection_state"], "MATCHED_APPROVED_NORMALIZED_LITERAL_CANDIDATES")
        self.assertEqual(record["source_declaration"]["plp_energy_star_flag_raw"], "Y")
        self.assertEqual(record["current_certification_state"], "NOT_EVALUATED")

    @patch("g2_energy_star_current_index_binding.load_replayed_rows")
    def test_current_index_pattern_is_matched_positionally(self, mocked):
        mocked.return_value = SCAN, [(row("RF23D*9600**"), SOURCE)]
        record = bind_current_index(MANIFEST, Path("ignored"))["records"][0]
        self.assertEqual(record["candidate_projection_state"], "MATCHED_CURRENT_INDEX_POSITIONAL_PATTERN_CANDIDATES")
        self.assertEqual(record["current_index_pattern_candidates"][0]["model_number_raw"], "RF23D*9600**")
        self.assertEqual(record["assessment"], "NOT_EVALUATED")

    @patch("g2_energy_star_current_index_binding.load_replayed_rows")
    def test_current_index_star_pattern_allows_digit_positions(self, mocked):
        mocked.return_value = SCAN, [(row("RF23DB9600**"), SOURCE)]
        record = bind_current_index(
            {**MANIFEST, "declarations": [{**MANIFEST["declarations"][0], "exact_sku": "RF23DB960012AA"}]},
            Path("ignored"),
        )["records"][0]
        self.assertEqual(record["candidate_projection_state"], "MATCHED_CURRENT_INDEX_POSITIONAL_PATTERN_CANDIDATES")

    @patch("g2_energy_star_current_index_binding.load_replayed_rows")
    def test_cross_run_capture_fails(self, mocked):
        mocked.return_value = {**SCAN, "source_run_id": "other"}, [(row("RF23DB9600QL"), SOURCE)]
        with self.assertRaisesRegex(ValueError, "runs differ"):
            bind_current_index(MANIFEST, Path("ignored"))


if __name__ == "__main__":
    unittest.main()

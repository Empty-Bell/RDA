from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_model_diagnostic_report import (  # noqa: E402
    build_report,
    observe_current_index,
    observe_us_market,
)


class ModelDiagnosticReportTests(unittest.TestCase):
    def test_preserves_full_and_approved_suffix_normalized_diagnostics(self):
        records = build_report()["records"]
        rf23 = next(record for record in records if record["exact_sku"] == "RF23DB9600QLAA")
        self.assertEqual(
            rf23["terminal_suffix_normalization"]["normalized_identifier"], "RF23DB9600QL"
        )
        self.assertEqual(rf23["full_sku_diagnostic"]["diagnostic"], "WITHHELD_LENGTH_MISMATCH")
        self.assertEqual(
            rf23["normalized_identifier_diagnostic"]["diagnostic"],
            "POSITIONAL_COMPATIBLE_DIAGNOSTIC_ONLY",
        )
        self.assertEqual(
            rf23["normalized_identifier_diagnostic"]["identity_state"], "NOT_EVALUATED"
        )
        self.assertEqual(rf23["model_pattern_inclusion"], "INCLUDED")
        self.assertEqual(rf23["epa_pd_id"], "2839420")
        self.assertEqual(rf23["current_certification_state"], "OBSERVED_CURRENT_CERTIFIED_INDEX")
        self.assertEqual(rf23["us_applicability_state"], "OBSERVED_US_MARKET")
        self.assertEqual(rf23["us_market_observation_scope"], "EPA_ROW_ONLY")
        self.assertEqual(rf23["assessment"], "NOT_EVALUATED")

    def test_nonincluded_skus_do_not_become_uncertified(self):
        record = next(r for r in build_report()["records"] if r["exact_sku"] == "RF18A5101SR/AA")
        self.assertEqual(record["model_pattern_inclusion"], "NOT_INCLUDED")
        self.assertEqual(record["current_index_observation_scope"], "EPA_ROW_ONLY")
        self.assertEqual(record["assessment"], "NOT_EVALUATED")

    def test_market_requires_literal_complete_token(self):
        for value in ("United States", "United States, Canada", "Canada, United States"):
            self.assertEqual(observe_us_market(value, source_status="PASS"), "OBSERVED_US_MARKET")
        for value in (
            None,
            "",
            "Canada",
            "US",
            "Not United States",
            "United States; Canada",
            "United States,",
            [],
        ):
            self.assertEqual(observe_us_market(value, source_status="PASS"), "NOT_EVALUATED")

    def test_source_failure_cannot_become_market_observation(self):
        with self.assertRaises(ValueError):
            observe_us_market("United States", source_status="FAIL")

    def test_current_index_requires_all_exact_keys(self):
        row = {
            "pd_id": "2839420",
            "brand_name": "Samsung",
            "model_number": "RF23D*9600**",
            "energy_star_model_identifier": "CB",
        }
        self.assertEqual(
            observe_current_index(row, row)["state"], "OBSERVED_CURRENT_CERTIFIED_INDEX"
        )
        self.assertEqual(
            observe_current_index(row, {**row, "brand_name": "Other"})["state"], "NOT_EVALUATED"
        )
        self.assertEqual(
            observe_current_index(row, {**row, "model_number": None})["state"], "NOT_EVALUATED"
        )

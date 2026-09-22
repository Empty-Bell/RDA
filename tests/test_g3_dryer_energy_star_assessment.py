import json
import tempfile
import unittest
from pathlib import Path

from scripts.epa_only_rules import epa_registration_state, model_pattern_candidate, publication_points
from scripts.g3_dryer_energy_star_assessment import build


def claim(sku, plp="Y", badge=True, spec=True):
    return {
        "exact_sku": sku,
        "plp_energy_star_flag_raw": plp,
        "rendered_attributed_badges_raw": ([{"src": "energy-star-logo-pdp.png"}] if badge else []),
        "pdp_logo_inspection_raw": "SUPPORTED_PRIMARY_SURFACE_COMPLETE",
        "pdp_visible_spec_energy_star_rows_raw": ([{"text": "ENERGY STAR Certification Yes"}] if spec else []),
        "pdp_spec_surface_inspection_raw": "SUPPORTED_VISIBLE_SPEC_TABLE_COMPLETE",
    }


class DryerEnergyStarAssessmentContract(unittest.TestCase):
    def test_epa_star_pattern_maps_sku_suffix_without_prefix_guessing(self):
        result = model_pattern_candidate("RF23D*9600**", "RF23DB9600QLAA")
        self.assertEqual(result["matched_prefix_raw"], "RF23DB9600QL")
        self.assertEqual(result["remaining_sku_suffix_raw"], "AA")
        self.assertIsNone(model_pattern_candidate("RF23D9600", "RF23DB9600QLAA"))

    def test_only_explicit_us_market_counts_and_blank_market_fails_closed(self):
        state, _ = epa_registration_state([{"markets_raw": "Canada"}], [])
        self.assertEqual(state, "ABSENT")
        state, _ = epa_registration_state([{"markets_raw": "Russia"}], [])
        self.assertEqual(state, "UNKNOWN")
        state, _ = epa_registration_state([{"markets_raw": "United States, Canada"}], [])
        self.assertEqual(state, "PRESENT")
        state, _ = epa_registration_state([{"markets_raw": "U.S."}], [])
        self.assertEqual(state, "PRESENT")
        state, _ = epa_registration_state([{"markets_raw": None}], [])
        self.assertEqual(state, "UNKNOWN")

    def test_approved_three_point_rules_and_dashboard_no_finding_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skus = ["REGISTERED1", "MISSING1", "UNREGISTERED1", "CANADA1", "UNCERTAIN1"]
            rows = [
                {"exact_sku": skus[0], "energy_star_claim_sources_raw": claim(skus[0]),
                 "dryer_epa_model_pattern_candidates": [{"markets_raw": "United States"}],
                 "combo_epa_model_pattern_candidates": []},
                {"exact_sku": skus[1], "energy_star_claim_sources_raw": claim(skus[1], badge=False),
                 "dryer_epa_model_pattern_candidates": [{"markets_raw": "US"}],
                 "combo_epa_model_pattern_candidates": []},
                {"exact_sku": skus[2], "energy_star_claim_sources_raw": claim(skus[2]),
                 "dryer_epa_model_pattern_candidates": [], "combo_epa_model_pattern_candidates": []},
                {"exact_sku": skus[3], "energy_star_claim_sources_raw": claim(skus[3], plp="N", badge=False, spec=False),
                 "dryer_epa_model_pattern_candidates": [{"markets_raw": "Canada"}],
                 "combo_epa_model_pattern_candidates": []},
                {"exact_sku": skus[4], "energy_star_claim_sources_raw": claim(skus[4], plp="N", badge=False, spec=False),
                 "dryer_epa_model_pattern_candidates": [{"markets_raw": None}],
                 "combo_epa_model_pattern_candidates": []},
            ]
            source = {"contract": "G3_DRYER_EPA_CLAIM_CANDIDATES_V1",
                      "status": "SOURCE_CANDIDATES_READY", "source_validation": "PASS",
                      "population_count": len(rows), "collection_run_id": "1",
                      "epa_capture_run_id": "2", "combo_epa_capture_run_id": "2", "rows": rows}
            source_path = root / "candidates.json"
            source_path.write_text(json.dumps(source), encoding="utf-8")
            result = build(source_path, root / "out")
            by_sku = {row["exact_sku"]: row for row in result["records"]}
            self.assertEqual(by_sku[skus[0]]["display_outcome"], "PASS")
            self.assertEqual(by_sku[skus[1]]["display_outcome"], "LOW")
            self.assertEqual(by_sku[skus[2]]["display_outcome"], "HIGH")
            self.assertEqual(by_sku[skus[3]]["energy_star_publication"]["outcome"], "NO_FINDING")
            self.assertEqual(by_sku[skus[3]]["display_outcome"], "PASS")
            self.assertEqual(by_sku[skus[4]]["display_outcome"], "NOT_EVALUATED")
            self.assertEqual(result["counts"], {"HIGH": 1, "MEDIUM": 0, "LOW": 1,
                                                "PASS": 2, "NOT_EVALUATED": 1})

    def test_negative_visible_spec_value_is_not_a_certification_claim(self):
        points_claim = claim("SKU1")
        points_claim["pdp_visible_spec_energy_star_rows_raw"] = [
            {"text": "ENERGY STAR Certification No", "cells": ["ENERGY STAR Certification", "No"]}
        ]
        points = publication_points(points_claim)
        self.assertEqual(points["spec_certification"]["state"], "ABSENT")


if __name__ == "__main__":
    unittest.main()

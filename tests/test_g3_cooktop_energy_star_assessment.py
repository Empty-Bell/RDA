import unittest

from scripts.g3_cooktop_energy_star_assessment import assess_record


def source_row(sku, candidates, plp="Y", badge=True, spec=True):
    return {
        "exact_sku": sku,
        "cooktop_epa_pattern_candidates": candidates,
        "energy_star_claim_sources_raw": {
            "exact_sku": sku,
            "plp_energy_star_flag_raw": plp,
            "rendered_attributed_badges_raw": ([{"src": "energy-star-logo.png"}] if badge else []),
            "pdp_logo_inspection_raw": "SUPPORTED_PRIMARY_SURFACE_COMPLETE",
            "pdp_visible_spec_energy_star_rows_raw": ([{"text": "ENERGY STAR Certified Yes"}] if spec else []),
            "pdp_spec_surface_inspection_raw": "SUPPORTED_VISIBLE_SPEC_TABLE_COMPLETE",
        },
    }


class CooktopEnergyStarAssessmentTests(unittest.TestCase):
    def test_registered_electric_model_with_all_points_passes(self):
        row = source_row("COOKTOP1", [{"markets_raw": "United States, Canada"}])
        result = assess_record(row)
        self.assertEqual(result["display_outcome"], "PASS")
        self.assertEqual(result["legal_applicability"], "NOT_EVALUATED")

    def test_registered_model_missing_any_publication_point_is_low(self):
        row = source_row("COOKTOP2", [{"markets_raw": "United States"}], badge=False)
        result = assess_record(row)
        self.assertEqual(result["display_outcome"], "LOW")

    def test_unregistered_model_with_any_claim_is_high(self):
        row = source_row("COOKTOP3", [], plp="N", badge=True, spec=False)
        result = assess_record(row)
        self.assertEqual(result["display_outcome"], "HIGH")

    def test_unregistered_model_with_no_claim_is_pass_for_dashboard(self):
        row = source_row("COOKTOP4", [], plp="N", badge=False, spec=False)
        result = assess_record(row)
        self.assertEqual(result["energy_star_publication"]["outcome"], "NO_FINDING")
        self.assertEqual(result["display_outcome"], "PASS")

    def test_non_us_only_match_is_not_a_us_registration(self):
        row = source_row("COOKTOP5", [{"markets_raw": "Canada"}], plp="N", badge=False, spec=False)
        result = assess_record(row)
        self.assertEqual(result["display_outcome"], "PASS")
        self.assertEqual(result["epa_current_registration"]["state"], "ABSENT")


if __name__ == "__main__":
    unittest.main()


import unittest

from scripts.g3_monitor_energy_star_assessment import assess_record


def source_row(sku, candidates, plp="N", badge=False, spec=False,
               logo_inspection="SUPPORTED_PRIMARY_SURFACE_COMPLETE",
               spec_inspection="SUPPORTED_VISIBLE_SPEC_TABLE_COMPLETE"):
    return {
        "exact_sku": sku,
        "epa_display_pattern_candidates": candidates,
        "energy_star_claim_sources_raw": {
            "exact_sku": sku,
            "plp_energy_star_flag_raw": plp,
            "rendered_attributed_badges_raw": ([{"src": "energy-star-logo.png"}] if badge else []),
            "pdp_logo_inspection_raw": logo_inspection,
            "pdp_visible_spec_energy_star_rows_raw": (
                [{"text": "ENERGY STAR Certified Yes"}] if spec else []),
            "pdp_spec_surface_inspection_raw": spec_inspection,
        },
    }


class MonitorEnergyStarAssessmentTests(unittest.TestCase):
    def test_registered_model_with_all_three_points_passes(self):
        row = source_row("LS1", [{"display_type_raw": "Monitor", "markets_raw": "United States", "match_rule": "LITERAL_PDP_SKU"}],
                         plp="Y", badge=True, spec=True)
        result = assess_record(row)
        self.assertEqual(result["display_outcome"], "PASS")
        self.assertEqual(result["legal_applicability"], "NOT_EVALUATED")

    def test_registered_model_missing_publication_points_is_low(self):
        row = source_row("LS2", [{"display_type_raw": "Monitor", "markets_raw": "United States",
                                  "match_rule": "PDP_SKU_WITH_SINGLE_LEADING_L_OMITTED"}])
        result = assess_record(row)
        self.assertEqual(result["display_outcome"], "LOW")
        self.assertEqual(result["epa_current_registration"]["state"], "PRESENT")

    def test_unregistered_model_with_any_claim_is_high(self):
        row = source_row("LS3", [], badge=True)
        self.assertEqual(assess_record(row)["display_outcome"], "HIGH")

    def test_unregistered_model_without_claims_is_dashboard_pass(self):
        result = assess_record(source_row("LS4", []))
        self.assertEqual(result["energy_star_publication"]["outcome"], "NO_FINDING")
        self.assertEqual(result["display_outcome"], "PASS")

    def test_incomplete_publication_evidence_does_not_pass(self):
        row = source_row("LS5", [], logo_inspection=None)
        self.assertEqual(assess_record(row)["display_outcome"], "NOT_EVALUATED")

    def test_signage_candidate_is_not_a_monitor_registration(self):
        row = source_row("LS6", [{"display_type_raw": "Signage Display", "markets_raw": "United States"}])
        result = assess_record(row)
        self.assertEqual(result["epa_current_registration"]["state"], "ABSENT")
        self.assertEqual(result["display_outcome"], "PASS")


if __name__ == "__main__":
    unittest.main()

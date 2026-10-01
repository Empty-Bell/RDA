import unittest

from scripts.g3_computer_energy_star_assessment import assess_record, computer_registration


def candidate(rule, markets="United States"):
    return {
        "model_pattern_candidate": {"match_rule": rule},
        "epa_row_raw": {"type_raw": "Notebook", "markets_raw": markets},
    }


class ComputerRegistrationScopeTests(unittest.TestCase):
    def test_confirmed_wrong_model_pdp_is_high_without_borrowing_its_logo(self):
        row = {
            "exact_sku": "NP740VJG-KG2US",
            "energy_star_claim_sources_raw": {"exact_sku": "NP740VJG-KG2US",
                                               "plp_energy_star_flag_raw": "Y"},
            "epa_computer_model_pattern_candidates": [],
            "pdp_identity_failure": {
                "requested_url": "https://www.samsung.com/us/computers/book-sku-np740vjg-kg2us",
                "final_url": "https://www.samsung.com/us/computers/book-sku-np960ujh-xg2us/",
            },
        }
        result = assess_record(row)
        self.assertEqual(result["display_outcome"], "HIGH")
        self.assertEqual(result["findings"][0]["issue_code"], "PDP_LINK_WRONG_MODEL")
        self.assertEqual(result["energy_star_publication"]["points"]["pdp_logo"]["state"], "UNKNOWN")

    def test_base_model_prefix_confirms_registration_per_approved_rule(self):
        state, markets = computer_registration([
            candidate("EPA_BASE_MODEL_PREFIX_HYPHEN_SUFFIX")
        ])
        self.assertEqual(state, "PRESENT")
        self.assertEqual(markets, ["US"])

    def test_explicit_model_match_with_us_market_can_confirm_registration(self):
        state, markets = computer_registration([
            candidate("EPA_LITERAL_OR_POSITIONAL_PATTERN")
        ])
        self.assertEqual(state, "PRESENT")
        self.assertEqual(markets, ["US"])

    def test_computer_specs_certification_field_is_not_applicable(self):
        row = {
            "exact_sku": "NP740VJG-KA1US",
            "energy_star_claim_sources_raw": {
                "exact_sku": "NP740VJG-KA1US",
                "plp_energy_star_flag_raw": "Y",
                "rendered_attributed_badges_raw": [{"src": "energy-star-logo.png"}],
                "pdp_logo_inspection_raw": "SUPPORTED_PRIMARY_SURFACE_COMPLETE",
                "pdp_spec_energy_star_claim_raw": [],
            },
            "epa_computer_model_pattern_candidates": [
                candidate("EPA_BASE_MODEL_PREFIX_HYPHEN_SUFFIX")
            ],
        }
        result = assess_record(row)
        self.assertEqual(result["energy_star_publication"]["points"]["spec_certification"]["state"],
                         "NOT_APPLICABLE")
        self.assertEqual(result["display_outcome"], "PASS")

    def test_computer_plp_absence_still_counts_when_specs_field_not_applicable(self):
        row = {
            "exact_sku": "NP740VJG-KA1US",
            "energy_star_claim_sources_raw": {
                "exact_sku": "NP740VJG-KA1US",
                "plp_energy_star_flag_raw": "N",
                "rendered_attributed_badges_raw": [],
                "pdp_logo_inspection_raw": None,
                "pdp_spec_energy_star_claim_raw": [],
            },
            "epa_computer_model_pattern_candidates": [
                candidate("EPA_BASE_MODEL_PREFIX_HYPHEN_SUFFIX")
            ],
        }
        result = assess_record(row)
        self.assertEqual(result["energy_star_publication"]["points"]["spec_certification"]["state"],
                         "NOT_APPLICABLE")
        self.assertEqual(result["display_outcome"], "LOW")
    
if __name__ == "__main__":
    unittest.main()

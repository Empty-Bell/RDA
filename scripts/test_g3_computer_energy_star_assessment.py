import unittest

from scripts.g3_computer_energy_star_assessment import assess_record, computer_registration


def candidate(product_type="Notebook", markets="United States, Canada"):
    return {"epa_row_raw": {"type_raw": product_type, "markets_raw": markets}}


def claim(plp=False, pdp=False, specs=False):
    return {
        "exact_sku": "NP960UJH-XG7US",
        "plp_energy_star_flag_raw": plp,
        "rendered_attributed_badges_raw": ([{"exact_sku": "NP960UJH-XG7US"}] if pdp else []),
        "pdp_logo_inspection_raw": "SUPPORTED_PRIMARY_SURFACE_COMPLETE",
        "pdp_spec_energy_star_claim_raw": ([{"text": "ENERGY STAR"}] if specs else []),
    }


def row(candidates, evidence):
    return {"exact_sku": "NP960UJH-XG7US", "epa_computer_model_pattern_candidates": candidates,
            "energy_star_claim_sources_raw": evidence, "pdp_product_facts_raw": {}}


class ComputerEnergyStarAssessmentTests(unittest.TestCase):
    def test_us_notebook_with_all_applicable_points_is_pass(self):
        result = assess_record(row([candidate()], claim(True, True, False)))
        self.assertEqual(result["display_outcome"], "PASS")
        self.assertEqual(result["energy_star_publication"]["points"]["spec_certification"]["state"],
                         "NOT_APPLICABLE")

    def test_registered_notebook_missing_plp_is_low(self):
        result = assess_record(row([candidate()], claim(False, True, False)))
        self.assertEqual(result["display_outcome"], "LOW")

    def test_no_matching_epa_row_with_a_publication_claim_is_high(self):
        result = assess_record(row([], claim(True, False, False)))
        self.assertEqual(result["display_outcome"], "HIGH")

    def test_no_registration_and_no_publication_is_displayed_as_pass(self):
        result = assess_record(row([], claim(False, False, False)))
        self.assertEqual(result["display_outcome"], "PASS")

    def test_non_notebook_or_unknown_market_does_not_become_a_negative_match(self):
        self.assertEqual(computer_registration([candidate("Slate/Tablet")])[0], "UNKNOWN")
        self.assertEqual(computer_registration([candidate(markets="United States, Canada")])[0], "PRESENT")
        self.assertEqual(computer_registration([candidate(markets="")])[0], "UNKNOWN")

    def test_unknown_pdp_inspection_does_not_create_absence(self):
        evidence = claim(True, False, False)
        evidence["pdp_logo_inspection_raw"] = "NOT_EVALUATED"
        result = assess_record(row([candidate()], evidence))
        self.assertEqual(result["display_outcome"], "NOT_EVALUATED")

    def test_computer_plp_absence_still_counts_when_specs_field_not_applicable(self):
        result = assess_record(row([candidate()], claim(False, True, False)))
        self.assertEqual(result["energy_star_publication"]["points"]["spec_certification"]["state"],
                         "NOT_APPLICABLE")
        self.assertEqual(result["display_outcome"], "LOW")


if __name__ == "__main__":
    unittest.main()

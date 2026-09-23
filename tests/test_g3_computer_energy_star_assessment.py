import unittest

from scripts.g3_computer_energy_star_assessment import computer_registration


def candidate(rule, markets="United States"):
    return {
        "model_pattern_candidate": {"match_rule": rule},
        "epa_row_raw": {"type_raw": "Notebook", "markets_raw": markets},
    }


class ComputerRegistrationScopeTests(unittest.TestCase):
    def test_base_model_prefix_does_not_confirm_retail_sku_registration(self):
        state, markets = computer_registration([
            candidate("EPA_BASE_MODEL_PREFIX_HYPHEN_SUFFIX")
        ])
        self.assertEqual(state, "UNKNOWN")
        self.assertEqual(markets, ["UNKNOWN"])

    def test_explicit_model_match_with_us_market_can_confirm_registration(self):
        state, markets = computer_registration([
            candidate("EPA_LITERAL_OR_POSITIONAL_PATTERN")
        ])
        self.assertEqual(state, "PRESENT")
        self.assertEqual(markets, ["PRESENT"])


if __name__ == "__main__":
    unittest.main()

import unittest

from scripts.g3_computer_epa_candidates import additional_patterns, computer_model_candidate


class ComputerCandidateRuleTests(unittest.TestCase):
    def test_model_number_matching_does_not_drop_or_normalize_leading_characters(self):
        self.assertIsNone(computer_model_candidate("NP960UJH*", "LNP960UJHXG7US"))
        self.assertIsNone(computer_model_candidate("NP960UJH*", "NP960XJHXG7US"))
        self.assertIsNotNone(computer_model_candidate("NP960UJH*", "NP960UJHXG7US"))

    def test_literal_epa_base_model_may_only_extend_at_an_exact_hyphen_boundary(self):
        result = computer_model_candidate("NP960UJH", "NP960UJH-XG7US")
        self.assertEqual(result["match_rule"], "EPA_BASE_MODEL_PREFIX_HYPHEN_SUFFIX")
        self.assertEqual(result["remaining_sku_suffix_raw"], "-XG7US")
        self.assertIsNone(computer_model_candidate("NP960UJH", "NP960UJH2-XG7US"))
        self.assertIsNone(computer_model_candidate("NP960UJH", "LNP960UJH-XG7US"))

    def test_additional_model_tokens_are_limited_to_explicit_model_like_entries(self):
        self.assertEqual(additional_patterns("NP960UJH*; NP960XJH-KA1US, legacy text"),
                         ["NP960UJH*", "NP960XJH-KA1US"])

    def test_positional_wildcard_is_not_a_fuzzy_or_internal_deletion_match(self):
        self.assertIsNone(computer_model_candidate("XE550XGA-KC*", "XE550XGA-CKC1US"))
        self.assertIsNotNone(computer_model_candidate("XE550XGA-KC*", "XE550XGA-KC1US"))


if __name__ == "__main__":
    unittest.main()

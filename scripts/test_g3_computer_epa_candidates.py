import unittest

from scripts.g3_computer_epa_candidates import additional_patterns
from scripts.epa_only_rules import model_pattern_candidate


class ComputerCandidateRuleTests(unittest.TestCase):
    def test_model_number_matching_does_not_drop_or_normalize_leading_characters(self):
        self.assertIsNone(model_pattern_candidate("NP960UJH*", "LNP960UJHXG7US"))
        self.assertIsNone(model_pattern_candidate("NP960UJH*", "NP960XJHXG7US"))
        self.assertIsNotNone(model_pattern_candidate("NP960UJH*", "NP960UJHXG7US"))

    def test_additional_model_tokens_are_limited_to_explicit_model_like_entries(self):
        self.assertEqual(additional_patterns("NP960UJH*; NP960XJH-KA1US, legacy text"),
                         ["NP960UJH*", "NP960XJH-KA1US"])

    def test_positional_wildcard_is_not_a_fuzzy_or_internal_deletion_match(self):
        self.assertIsNone(model_pattern_candidate("XE550XGA-KC*", "XE550XGA-CKC1US"))
        self.assertIsNotNone(model_pattern_candidate("XE550XGA-KC*", "XE550XGA-KC1US"))


if __name__ == "__main__":
    unittest.main()

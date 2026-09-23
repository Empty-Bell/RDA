import unittest

from scripts.g3_monitor_epa_candidates import additional_model_patterns, monitor_model_pattern_candidate
from scripts.epa_only_rules import model_pattern_candidate


class MonitorAdditionalModelEvidenceTests(unittest.TestCase):
    def test_extracts_only_standalone_epa_model_tokens(self):
        raw = ("LF27T450FQNX**,LF27T450FQNX**; "
               "* can be any alphanumeric character; S27B804PXN,S27B804PXN; "
               "Same as basic model except model designation.")
        self.assertEqual(additional_model_patterns(raw), [
            "LF27T450FQNX**", "S27B804PXN"])

    def test_deduplicates_repeated_source_tokens(self):
        self.assertEqual(additional_model_patterns("S24D400GA*,S24D400GA*"), ["S24D400GA*"])

    def test_explicit_epa_alternate_pattern_uses_shared_positional_rule(self):
        pattern = additional_model_patterns("LS27B804PX*,LS27B804PX*")[0]
        candidate = model_pattern_candidate(pattern, "LS27B804PXNXGO")
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["candidate_basis"], "POSITIONAL_PREFIX_PATTERN; EACH * = ONE A-Z/0-9 CHARACTER")

    def test_does_not_match_a_pattern_found_only_in_explanation_prose(self):
        raw = "* can be any alphanumeric character; Same as basic model except model designation"
        self.assertEqual(additional_model_patterns(raw), [])

    def test_monitor_matching_omits_exactly_one_approved_leading_l(self):
        match = monitor_model_pattern_candidate("S27B804PX*", "LS27B804PXNXGO")
        self.assertIsNotNone(match)
        self.assertEqual(match["match_rule"], "PDP_SKU_WITH_SINGLE_LEADING_L_OMITTED")
        self.assertEqual(match["candidate_basis"], "POSITIONAL_PREFIX_PATTERN; EACH * = ONE A-Z/0-9 CHARACTER")

    def test_monitor_matching_keeps_literal_match_and_does_not_strip_extra_characters(self):
        literal = monitor_model_pattern_candidate("LS27B804PX*", "LS27B804PXNXGO")
        self.assertEqual(literal["match_rule"], "LITERAL_PDP_SKU")
        already_without_l = monitor_model_pattern_candidate("S27B804PX*", "S27B804PXNXGO")
        self.assertEqual(already_without_l["match_rule"], "LITERAL_PDP_SKU")
        self.assertIsNone(monitor_model_pattern_candidate("S27B804PX*", "LXS27B804PXNXGO"))


if __name__ == "__main__":
    unittest.main()


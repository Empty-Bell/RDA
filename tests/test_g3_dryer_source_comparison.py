"""Dryer source-join candidate boundaries; no compliance decisions."""

import unittest

from scripts.g3_dryer_source_comparison import label_model_display, positional_prefix_candidate


class DryerSourceCandidateJoinContract(unittest.TestCase):
    def test_positional_pattern_is_candidate_and_preserves_sku_suffix(self):
        candidate = positional_prefix_candidate("DV53BB8900HDA*", "DV53BB8900HDA2")
        self.assertEqual(candidate["matched_prefix_raw"], "DV53BB8900HDA2")
        self.assertEqual(candidate["remaining_sku_suffix_raw"], "")
        self.assertIn("CANDIDATE", candidate["candidate_basis"])

    def test_pattern_length_must_match_character_positions(self):
        candidate = positional_prefix_candidate("DV53BB8900H*", "DV53BB8900HDA2")
        self.assertEqual(candidate["remaining_sku_suffix_raw"], "A2")
        self.assertIsNone(positional_prefix_candidate("DV53BB8900HDA*", "DV53BB8900HDX2"))

    def test_wrong_literal_identity_is_not_silently_normalized(self):
        self.assertIsNone(positional_prefix_candidate("DV53-BB8900HDA*", "DV53BB8900HDA2"))

    def test_only_sku_compatible_label_pattern_is_shown_as_pattern_candidate(self):
        document = {
            "model_inclusion_candidates": [{"pattern_raw": "WD53DBA9**H*"}],
            "model_candidates_raw": [{"value_raw": "DC68-04515A-00"},
                                      {"value_raw": "WD53DBA9**H*"}],
        }
        self.assertEqual(label_model_display(document), ("WD53DBA9**H*", "DC68-04515A-00"))


if __name__ == "__main__":
    unittest.main()

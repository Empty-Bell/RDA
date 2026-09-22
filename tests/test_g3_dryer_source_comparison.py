"""Dryer source-join candidate boundaries; no compliance decisions."""

import unittest

from scripts.g3_dryer_source_comparison import positional_prefix_candidate


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


if __name__ == "__main__":
    unittest.main()

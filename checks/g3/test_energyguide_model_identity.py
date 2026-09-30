import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from energyguide_model_identity import matches_printed_model  # noqa: E402
from g3_washer_source_comparison import label_model_match as washer_label_match, model_prefix_match as washer_epa_match  # noqa: E402
from g3_tv_source_comparison import label_model_match as tv_label_match, model_prefix_match as tv_epa_match  # noqa: E402


class PrintedModelIdentityTests(unittest.TestCase):
    def test_trailing_stars_and_pdp_suffix_may_have_different_lengths(self):
        self.assertTrue(matches_printed_model("DW80BB7070*", "DW80BB707012AA"))
        self.assertTrue(matches_printed_model("DW80CG54******", "DW80CG5450SRAA"))
        self.assertTrue(matches_printed_model("RF27CG5400***", "RF27CG5400SRAA"))

    def test_fixed_character_after_internal_stars_still_matters(self):
        self.assertTrue(matches_printed_model("DW80B70**U*", "DW80B7070US/AA"))
        self.assertFalse(matches_printed_model("DW80B70**A*", "DW80B7070US/AA"))
        self.assertFalse(matches_printed_model("DW80CG54******", "DW80CB5450SRAA"))
        self.assertFalse(matches_printed_model("******", "DW80CG5450SRAA"))
        self.assertFalse(matches_printed_model("D*", "DW80CG5450SRAA"))
        self.assertFalse(matches_printed_model("DW*", "DW80CG5450SRAA"))

    def test_washer_and_tv_label_apply_rule_without_changing_epa_rule(self):
        for label, epa in ((washer_label_match, washer_epa_match), (tv_label_match, tv_epa_match)):
            self.assertIsNotNone(label("DW80CG54******", "DW80CG5450SRAA"))
            self.assertIsNone(epa("DW80CG54**********", "DW80CG5450SRAA"))


if __name__ == "__main__":
    unittest.main()

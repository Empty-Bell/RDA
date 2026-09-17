from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_samsung_suffix import normalize_terminal_aa  # noqa: E402


class SamsungSuffixTests(unittest.TestCase):
    def test_terminal_aa_and_slash_aa_are_observationally_normalized(self):
        self.assertEqual(
            normalize_terminal_aa("RF23DB9600QLAA")["normalized_identifier"], "RF23DB9600QL"
        )
        result = normalize_terminal_aa("RF18A5101SR/AA")
        self.assertEqual(result["normalized_identifier"], "RF18A5101SR")
        self.assertEqual(result["removed_terminal_suffix"], "/AA")
        self.assertEqual(result["identity_state"], "NOT_EVALUATED")

    def test_only_exact_uppercase_terminal_forms_are_accepted(self):
        for value in ("RF23DB9600QL", "RF23DB9600QL/A", "RF23DB9600QL/AAZ", "rf23DB9600QLAA", "AA"):
            with self.assertRaises(ValueError):
                normalize_terminal_aa(value)

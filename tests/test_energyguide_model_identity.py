import unittest

from scripts.energyguide_model_identity import matches_printed_model


class PrintedModelIdentityTest(unittest.TestCase):
    def test_internal_wildcard_with_later_fixed_positions(self):
        self.assertTrue(matches_printed_model("RF23D*9600**", "RF23DB9600QLAA", strip_terminal_aa=True))
        self.assertFalse(matches_printed_model("RF23D*9600**", "RF23DB9700QLAA", strip_terminal_aa=True))
        self.assertFalse(matches_printed_model("RF23D*9600**", "RF24DB9600QLAA", strip_terminal_aa=True))

    def test_short_prefix_without_later_identity_remains_unresolved(self):
        self.assertFalse(matches_printed_model("RF23D*****", "RF23DB9600QLAA", strip_terminal_aa=True))
        self.assertFalse(matches_printed_model("RF23*96***", "RF23DB9600QLAA", strip_terminal_aa=True))

    def test_existing_trailing_prefix_rule(self):
        self.assertTrue(matches_printed_model("RF23DB*", "RF23DB9600QLAA", strip_terminal_aa=True))


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_model_diagnostic_report import build_report  # noqa: E402


class ModelDiagnosticReportTests(unittest.TestCase):
    def test_preserves_full_and_approved_suffix_normalized_diagnostics(self):
        records = build_report()["records"]
        rf23 = next(record for record in records if record["exact_sku"] == "RF23DB9600QLAA")
        self.assertEqual(
            rf23["terminal_suffix_normalization"]["normalized_identifier"], "RF23DB9600QL"
        )
        self.assertEqual(rf23["full_sku_diagnostic"]["diagnostic"], "WITHHELD_LENGTH_MISMATCH")
        self.assertEqual(
            rf23["normalized_identifier_diagnostic"]["diagnostic"],
            "POSITIONAL_COMPATIBLE_DIAGNOSTIC_ONLY",
        )
        self.assertEqual(
            rf23["normalized_identifier_diagnostic"]["identity_state"], "NOT_EVALUATED"
        )

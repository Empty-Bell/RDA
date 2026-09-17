from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_refrigerator_pattern_capture import (  # noqa: E402
    compatible_pattern_pairs,
    validate_refrigerator_row,
)


def feed() -> dict:
    return {
        "targets": [
            {
                "exact_sku": "RF23DB9600QLAA",
                "pdp_identity_state": "VERIFIED_EXACT_IDENTITY",
                "source_run_id": "run",
            }
        ]
    }


def projection(pattern: str = "RF23D*9600**") -> dict:
    return {
        "records": [
            {
                "exact_sku": {
                    "exact_sku_raw": "RF23DB9600QLAA",
                    "approved_normalized_identifier": "RF23DB9600QL",
                },
                "unresolved_pattern_references": [
                    {"pd_id": "2839420", "model_number_raw": pattern}
                ],
            }
        ]
    }


class RefrigeratorPatternCaptureTests(unittest.TestCase):
    def test_selects_only_positionally_compatible_pattern_rows(self):
        pairs = compatible_pattern_pairs(feed(), projection(), "a" * 64)
        self.assertEqual(pairs[0]["current_index_reference"]["pd_id"], "2839420")
        self.assertEqual(compatible_pattern_pairs(feed(), projection("OTHER*"), "a" * 64), [])

    def test_target_must_remain_in_same_run_feed(self):
        bad = projection()
        bad["records"][0]["exact_sku"]["exact_sku_raw"] = "OTHERAA"
        with self.assertRaisesRegex(ValueError, "missing"):
            compatible_pattern_pairs(feed(), bad, "a" * 64)

    def test_pd_id_query_rejects_empty_ambiguous_or_wrong_row(self):
        row = {"pd_id": "2839420"}
        self.assertEqual(validate_refrigerator_row("2839420", [row]), row)
        for rows in ([], [row, row], [{"pd_id": "1"}]):
            with self.assertRaises(ValueError):
                validate_refrigerator_row("2839420", rows)


if __name__ == "__main__":
    unittest.main()

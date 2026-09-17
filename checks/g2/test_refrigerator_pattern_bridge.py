from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_refrigerator_pattern_bridge import (  # noqa: E402
    bridge_pattern_candidate,
    build_refrigerator_target_feed,
)


def pdp(sku: str, status: str = "VERIFIED_EXACT_IDENTITY") -> dict:
    return {
        "exact_sku": sku,
        "status": status,
        "bridge": {"url": "https://www.samsung.com/us/example", "sha256": "a" * 64},
    }


def epa_row() -> dict:
    return {
        "pd_id": "2839420",
        "brand_name": "Samsung",
        "model_number": "RF23D*9600**",
        "energy_star_model_identifier": "CB",
    }


class RefrigeratorPatternBridgeTests(unittest.TestCase):
    def test_same_run_feed_keeps_only_verified_pdp_targets(self):
        feed = build_refrigerator_target_feed(
            [pdp("RF23DB9600QLAA"), pdp("FAILED", "FAILED")], "execution-1"
        )
        self.assertEqual(feed["targets"][0]["source_run_id"], "execution-1")
        self.assertEqual([target["exact_sku"] for target in feed["targets"]], ["RF23DB9600QLAA"])

    def test_four_key_binding_allows_only_provenance_bound_pattern_candidate(self):
        target = build_refrigerator_target_feed([pdp("RF23DB9600QLAA")], "execution-1")["targets"][
            0
        ]
        result = bridge_pattern_candidate(
            target,
            epa_row(),
            [epa_row()],
            execution_id="execution-1",
            refrigerator_metadata_sha256="b" * 64,
        )
        self.assertEqual(result["pattern_candidate_state"], "PROVENANCE_BOUND_POSITIONAL_CANDIDATE")
        self.assertEqual(result["current_certification_state"], "NOT_EVALUATED")
        self.assertEqual(result["assessment"], "NOT_EVALUATED")

    def test_mixed_run_or_four_key_mismatch_is_rejected(self):
        target = build_refrigerator_target_feed([pdp("RF23DB9600QLAA")], "execution-1")["targets"][
            0
        ]
        with self.assertRaisesRegex(ValueError, "provenance"):
            bridge_pattern_candidate(
                target,
                epa_row(),
                [epa_row()],
                execution_id="execution-2",
                refrigerator_metadata_sha256="b" * 64,
            )
        with self.assertRaisesRegex(ValueError, "mismatch"):
            bridge_pattern_candidate(
                target,
                epa_row(),
                [{**epa_row(), "energy_star_model_identifier": "OTHER"}],
                execution_id="execution-1",
                refrigerator_metadata_sha256="b" * 64,
            )
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            bridge_pattern_candidate(
                target,
                epa_row(),
                [epa_row(), epa_row()],
                execution_id="execution-1",
                refrigerator_metadata_sha256="b" * 64,
            )


if __name__ == "__main__":
    unittest.main()

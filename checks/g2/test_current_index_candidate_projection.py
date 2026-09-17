from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_current_index_candidate_projection import project_candidates  # noqa: E402


def scan() -> dict:
    return {
        "query_completeness": "COMPLETE_OBSERVED_QUERY",
        "current_certification_state": "NOT_EVALUATED",
        "assessment": "NOT_EVALUATED",
        "source_run_id": "run-1",
    }


def row(model: str, source_row_id: str) -> tuple[dict, dict]:
    return (
        {
            "source_row_id": source_row_id,
            "pd_id": "pd-" + source_row_id,
            "brand_name": "Samsung",
            "model_number": model,
            "energy_star_model_identifier": "cb-" + source_row_id,
        },
        {"name": "page-0000", "body_sha256": "a" * 64},
    )


def target(sku: str) -> dict:
    return {
        "exact_sku": sku,
        "pdp_identity_state": "VERIFIED_EXACT_IDENTITY",
        "source_run_id": "run-1",
        "source_evidence_ids": ["e-target"],
    }


class CurrentIndexCandidateProjectionTests(unittest.TestCase):
    def test_preserves_all_raw_and_normalized_literal_candidates(self):
        result = project_candidates(
            scan(),
            [row("RF23DB9600QLAA", "1"), row("RF23DB9600QL", "2")],
            [target("RF23DB9600QLAA")],
        )
        record = result["records"][0]
        self.assertEqual(record["candidate_projection_state"], "MATCHED_RAW_LITERAL_CANDIDATES")
        self.assertEqual(
            [candidate["source_row_id"] for candidate in record["raw_literal_candidates"]], ["1"]
        )
        self.assertEqual(
            [
                candidate["source_row_id"]
                for candidate in record["approved_normalized_literal_candidates"]
            ],
            ["2"],
        )
        self.assertEqual(record["current_certification_state"], "NOT_EVALUATED")

    def test_pattern_presence_withholds_complete_no_match(self):
        result = project_candidates(scan(), [row("RF23D*9600**", "1")], [target("RF18A5101SR/AA")])
        record = result["records"][0]
        self.assertEqual(
            record["candidate_projection_state"], "UNRESOLVED_PATTERN_ENCODINGS_PRESENT"
        )
        self.assertEqual(record["unresolved_pattern_references"][0]["source_row_id"], "1")
        no_pattern = project_candidates(scan(), [row("OTHER", "2")], [target("RF18A5101SR/AA")])
        self.assertEqual(
            no_pattern["records"][0]["candidate_projection_state"],
            "COMPLETE_NO_LITERAL_OR_PATTERN_CANDIDATE",
        )

    def test_rejects_mixed_run_or_unverified_target(self):
        with self.assertRaisesRegex(ValueError, "provenance"):
            project_candidates(
                scan(), [row("OTHER", "1")], [{**target("SKUAA"), "source_run_id": "run-2"}]
            )
        with self.assertRaisesRegex(ValueError, "verified PDP"):
            project_candidates(
                scan(), [row("OTHER", "1")], [{**target("SKUAA"), "pdp_identity_state": "FAILED"}]
            )
        with self.assertRaisesRegex(ValueError, "duplicated"):
            project_candidates(scan(), [row("OTHER", "1")], [target("SKUAA"), target("SKUAA")])


if __name__ == "__main__":
    unittest.main()

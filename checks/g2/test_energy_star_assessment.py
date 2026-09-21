from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_energy_star_assessment import build_assessment  # noqa: E402


def review_record(sku, family):
    return {
        "exact_sku": sku,
        "plp_logo_source": {"raw_value": "Y"},
        "pdp_logo_source": {"raw_value": "Y"},
        "pdp_spec_certification_source": {"raw_rows": []},
        "source_evidence_refs": {
            "plp_logo_source": {}, "pdp_logo_source": {},
            "pdp_spec_certification_source": {"full_specs_collection": "COMPLETE_EXACT_SKU_SPECS"},
        },
        "epa_current_index_candidate": {
            "candidate_projection_state": "COMPLETE_NO_LITERAL_OR_PATTERN_CANDIDATE",
            "source_declaration": {"source_family_id": family, "representative_sku": sku},
        },
    }


class EnergyStarAssessmentTests(unittest.TestCase):
    def test_high_clusters_preserve_each_exact_sku_finding(self):
        review = {
            "contract": "G2_ENERGY_STAR_THREE_POINT_INPUT_REVIEW_ONLY_V1",
            "source_run_id": "run-1",
            "current_index_query_completeness": "COMPLETE_OBSERVED_QUERY",
            "records": [review_record("SKU-A", "GROUP-1"), review_record("SKU-B", "GROUP-1")],
        }
        result = build_assessment(
            review, expected_exact_skus=2, query_completeness="COMPLETE_OBSERVED_QUERY"
        )
        self.assertEqual(result["counts"]["HIGH"], 2)
        cluster = result["review_clusters"]["HIGH"][0]
        self.assertEqual(cluster["source_family_id"], "GROUP-1")
        self.assertEqual(cluster["exact_skus"], ["SKU-A", "SKU-B"])
        self.assertEqual(cluster["exact_sku_count"], 2)


if __name__ == "__main__":
    unittest.main()

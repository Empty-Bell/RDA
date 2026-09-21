from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_energy_star_review_report import render_review_report  # noqa: E402


class EnergyStarReviewReportTests(unittest.TestCase):
    def test_renders_counts_clusters_and_low_points(self):
        assessment = {
            "contract": "G2_ENERGY_STAR_THREE_POINT_ASSESSMENT_V1",
            "source_run_id": "run-1",
            "coverage": {"expected_exact_skus": 2, "evaluated_records": 2},
            "counts": {"HIGH": 1, "LOW": 1},
            "review_clusters": {"HIGH": [{
                "source_family_id": "GROUP-1", "representative_sku": "SKU-H",
                "exact_sku_count": 1, "exact_skus": ["SKU-H"],
            }]},
            "records": [{"exact_sku": "SKU-L", "severity": "LOW", "publication_points": {
                "plp_logo": {"state": "ABSENT"}, "pdp_logo": {"state": "PRESENT"},
            }}],
        }
        report = render_review_report(assessment)
        self.assertIn("| 2 | 2 | 0 | 1 | 1 | 0 | 0 |", report)
        self.assertIn("| GROUP-1 | SKU-H | 1 | SKU-H |", report)
        self.assertIn("| SKU-L | plp_logo |", report)


if __name__ == "__main__":
    unittest.main()

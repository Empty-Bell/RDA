from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_energy_star_report_adapter import (  # noqa: E402
    add_energy_star_section,
    attach_energy_star_assessment,
)


class EnergyStarReportAdapterTests(unittest.TestCase):
    def setUp(self):
        self.bundle = {
            "manifest": {"run_id": "run-1", "git_sha": "a" * 40},
            "products": [{"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}],
        }
        self.manifest = {
            "contract": "G2_ENERGY_STAR_DIRECT_SOURCE_DECLARATIONS_V1",
            "status": "PASS", "run_id": "run-1", "github_run_id": "123",
            "git_sha": "a" * 40,
        }
        self.assessment = {
            "contract": "G2_ENERGY_STAR_THREE_POINT_ASSESSMENT_V1",
            "source_run_id": "run-1",
            "coverage": {"expected_exact_skus": 2, "evaluated_records": 2},
            "counts": {"HIGH": 1, "NO_FINDING": 1},
            "review_clusters": {"HIGH": []},
            "records": [
                {"exact_sku": "SKU-A", "outcome": "HIGH", "severity": "HIGH",
                 "issue_code": "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE"},
                {"exact_sku": "SKU-B", "outcome": "NO_FINDING", "severity": None,
                 "issue_code": None},
            ],
        }
        self.file = tempfile.NamedTemporaryFile(delete=False)
        self.file.write(b"assessment evidence")
        self.file.close()

    def tearDown(self):
        Path(self.file.name).unlink(missing_ok=True)

    def section(self):
        return attach_energy_star_assessment(
            self.bundle, self.assessment, self.manifest, self.file.name,
            github_run_id="123", artifact_reference="assessment.json",
        )

    def test_attaches_separate_section_and_preserves_unassessed_summary(self):
        section = self.section()
        report = {"run_id": "run-1", "assessment_enabled": False,
                  "counts": {"finding_count": 0},
                  "rows": [{"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}]}
        add_energy_star_section(report, section)
        self.assertEqual(report["counts"]["finding_count"], 0)
        self.assertEqual(section["display_counts"]["PASS"], 1)
        self.assertEqual(section["display_counts"]["HIGH"], 1)
        self.assertEqual(section["overall_product_compliance"], "NOT_EVALUATED")

    def test_rejects_mixed_execution_or_commit(self):
        self.assessment["source_run_id"] = "other-run"
        with self.assertRaisesRegex(ValueError, "execution IDs"):
            self.section()
        self.assessment["source_run_id"] = "run-1"
        self.manifest["git_sha"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "commits"):
            self.section()

    def test_rejects_sku_coverage_or_count_mismatch(self):
        self.assessment["records"][1]["exact_sku"] = "SKU-C"
        with self.assertRaisesRegex(ValueError, "SKU coverage"):
            self.section()
        self.assessment["records"][1]["exact_sku"] = "SKU-B"
        self.assessment["counts"]["HIGH"] = 2
        with self.assertRaisesRegex(ValueError, "counts"):
            self.section()

    def test_rejects_incomplete_coverage_and_cross_report_join(self):
        self.assessment["coverage"]["evaluated_records"] = 1
        with self.assertRaisesRegex(ValueError, "complete exact SKU"):
            self.section()
        self.assessment["coverage"]["evaluated_records"] = 2
        report = {"run_id": "run-1", "assessment_enabled": False,
                  "rows": [{"exact_sku": "SKU-A"}]}
        with self.assertRaisesRegex(ValueError, "report section SKU coverage"):
            add_energy_star_section(report, self.section())


if __name__ == "__main__":
    unittest.main()

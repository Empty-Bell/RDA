from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from g2_energyguide_numeric_report_adapter import add_numeric_section, attach_numeric_assessment  # noqa: E402


class NumericReportAdapterTests(unittest.TestCase):
    def setUp(self):
        self.bundle = {"manifest": {"run_id": "run-1"}, "products": [
            {"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}]}
        self.assessment = {
            "contract": "G2_ENERGYGUIDE_NUMERIC_ASSESSMENT_V1", "status": "PASS",
            "assessment_enabled": True, "source": {"execution_run_id": "run-1"},
            "counts": {"display": {"PASS": 1, "MEDIUM": 1, "LOW": 0, "NOT_EVALUATED": 0}},
            "records": [
                {"exact_sku": "SKU-A", "display_outcome": "MEDIUM", "findings": [{"issue_code": "PDP_ENERGYGUIDE_CAPACITY_MISMATCH"}]},
                {"exact_sku": "SKU-B", "display_outcome": "PASS", "findings": []},
            ],
        }
        self.file = tempfile.NamedTemporaryFile(delete=False)
        self.file.write(b"numeric assessment")
        self.file.close()

    def tearDown(self):
        Path(self.file.name).unlink(missing_ok=True)

    def test_attaches_complete_section_without_enabling_whole_product_compliance(self):
        section = attach_numeric_assessment(self.bundle, self.assessment, self.file.name)
        report = {"run_id": "run-1", "assessment_enabled": False,
                  "rows": [{"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}]}
        add_numeric_section(report, section)
        self.assertEqual(section["coverage"], {"expected_exact_skus": 2, "evaluated_records": 2})
        self.assertEqual(report["energyguide_numeric"]["counts"]["display"]["MEDIUM"], 1)
        self.assertEqual(section["overall_product_compliance"], "NOT_EVALUATED")

    def test_rejects_mixed_run_or_coverage(self):
        self.assessment["source"]["execution_run_id"] = "other"
        with self.assertRaisesRegex(ValueError, "execution ID"):
            attach_numeric_assessment(self.bundle, self.assessment, self.file.name)
        self.assessment["source"]["execution_run_id"] = "run-1"
        self.assessment["records"][1]["exact_sku"] = "SKU-C"
        with self.assertRaisesRegex(ValueError, "SKU coverage"):
            attach_numeric_assessment(self.bundle, self.assessment, self.file.name)

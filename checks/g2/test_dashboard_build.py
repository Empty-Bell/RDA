from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_dashboard_build import build  # noqa: E402


class DashboardBuildTests(unittest.TestCase):
    def inputs(self):
        bundle = {"manifest": {"run_id": "run-1", "git_sha": "a", "runner": "ubuntu-24.04"}}
        records = [{"exact_sku": "SKU-A", "controls": {"energy_star_publication": {"outcome": "HIGH"}, "energyguide_numeric": {"outcome": "PASS"}, "energyguide_model_pattern": {"outcome": "OUT_OF_SCOPE"}}, "findings": [{"control": "ENERGY_STAR_PUBLICATION", "severity": "HIGH", "issue_code": "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE"}]}, {"exact_sku": "SKU-B", "controls": {"energy_star_publication": {"outcome": "PASS"}, "energyguide_numeric": {"outcome": "LOW"}, "energyguide_model_pattern": {"outcome": "PASS"}}, "findings": [{"control": "ENERGYGUIDE_NUMERIC", "severity": "LOW", "issue_code": "PDP_ANNUAL_ENERGY_MISSING"}]}]
        report = {"run_id": "run-1", "rows": [{"exact_sku": item["exact_sku"], "refrigerator_control_summary": {"controls": item["controls"], "findings": item["findings"]}} for item in records], "refrigerator_control_summary": {"contract": "G2_REFRIGERATOR_CONTROL_SUMMARY_V1", "source_run_id": "run-1", "counts": {"finding_count": 2, "affected_sku_count": 2, "findings_by_severity": {"HIGH": 1, "MEDIUM": 0, "LOW": 1}}, "records": records}}
        return bundle, report

    def test_builds_same_run_data_and_exports(self):
        bundle, report = self.inputs()
        with tempfile.TemporaryDirectory() as directory:
            result = build(bundle, report, directory)
            self.assertEqual(result["summary"]["finding_count"], 2)
            self.assertIn("data/findings.json", result["files"])
            self.assertIn("report_data.csv", result["files"])

    def test_rejects_mixed_runs(self):
        bundle, report = self.inputs()
        report["refrigerator_control_summary"]["source_run_id"] = "other"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "different executions"):
                build(bundle, report, directory)

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_refrigerator_control_summary import add_control_summary, build_summary  # noqa: E402


class RefrigeratorControlSummaryTests(unittest.TestCase):
    def report(self):
        return {"run_id": "run-1", "assessment_enabled": False, "rows": [{"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}],
                "energy_star_publication": {"source_run_id": "run-1", "records": [
                    {"exact_sku": "SKU-A", "outcome": "HIGH", "severity": "HIGH", "issue_code": "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE"},
                    {"exact_sku": "SKU-B", "outcome": "PASS", "severity": None, "issue_code": None}]},
                "energyguide_numeric": {"source_run_id": "run-1", "records": [
                    {"exact_sku": "SKU-A", "display_outcome": "MEDIUM", "findings": [{"severity": "MEDIUM", "issue_code": "PDP_ENERGYGUIDE_CAPACITY_MISMATCH"}]},
                    {"exact_sku": "SKU-B", "display_outcome": "PASS", "findings": []}]},
                "energyguide_model_pattern": {"source_run_id": "run-1", "records": [
                    {"exact_sku": "SKU-B", "display_outcome": "PASS", "assessment": "MODEL_PATTERN_INCLUDED"}]}}

    def test_joins_controls_without_creating_a_product_verdict(self):
        report = self.report()
        summary = build_summary(report)
        add_control_summary(report, summary)
        self.assertEqual(summary["counts"], {"finding_count": 2, "affected_sku_count": 1,
                                                "findings_by_severity": {"HIGH": 1, "MEDIUM": 1, "LOW": 0}})
        self.assertEqual(report["rows"][0]["refrigerator_control_summary"]["controls"]["energyguide_model_pattern"]["outcome"], "OUT_OF_SCOPE")
        self.assertEqual(report["rows"][1]["refrigerator_control_summary"]["controls"]["energyguide_model_pattern"]["outcome"], "PASS")
        self.assertFalse(report["assessment_enabled"])

    def test_rejects_mixed_run_or_incomplete_control_coverage(self):
        report = self.report()
        report["energyguide_numeric"]["source_run_id"] = "other"
        with self.assertRaisesRegex(ValueError, "another execution"):
            build_summary(report)
        report = self.report()
        report["energy_star_publication"]["records"].pop()
        with self.assertRaisesRegex(ValueError, "coverage"):
            build_summary(report)

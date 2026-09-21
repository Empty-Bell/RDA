from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_dashboard_build import build  # noqa: E402
from g2_refrigerator_acceptance import validate  # noqa: E402
from g2_refrigerator_control_summary import add_control_summary, build_summary  # noqa: E402


class RefrigeratorAcceptanceTests(unittest.TestCase):
    def inputs(self):
        bundle = {"manifest": {"run_id": "run-1", "runner": "ubuntu-24.04"}, "products": [{"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}]}
        report = {"run_id": "run-1", "assessment_enabled": False, "rows": [{"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}],
                  "energy_star_publication": {"source_run_id": "run-1", "records": [
                      {"exact_sku": "SKU-A", "outcome": "HIGH", "severity": "HIGH", "issue_code": "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE"},
                      {"exact_sku": "SKU-B", "outcome": "PASS", "severity": None, "issue_code": None}]},
                  "energyguide_numeric": {"source_run_id": "run-1", "records": [
                      {"exact_sku": "SKU-A", "display_outcome": "PASS", "findings": []},
                      {"exact_sku": "SKU-B", "display_outcome": "LOW", "findings": [{"severity": "LOW", "issue_code": "PDP_ANNUAL_ENERGY_MISSING"}]}]},
                  "energyguide_model_pattern": {"source_run_id": "run-1", "records": []}}
        add_control_summary(report, build_summary(report))
        return bundle, report

    def test_accepts_a_dashboard_that_replays_one_run(self):
        bundle, report = self.inputs()
        with tempfile.TemporaryDirectory() as directory:
            build(bundle, report, directory)
            result = validate(bundle, report, directory)
        self.assertEqual(result["exact_sku_count"], 2)
        self.assertEqual(result["finding_count"], 2)

    def test_rejects_missing_compact_evidence(self):
        bundle, report = self.inputs()
        with tempfile.TemporaryDirectory() as directory:
            build(bundle, report, directory)
            evidence = next((Path(directory) / "evidence").rglob("finding.json"))
            evidence.unlink()
            with self.assertRaisesRegex(ValueError, "evidence file is missing"):
                validate(bundle, report, directory)

    def test_rejects_dashboard_coverage_drift(self):
        bundle, report = self.inputs()
        with tempfile.TemporaryDirectory() as directory:
            build(bundle, report, directory)
            report["rows"].pop()
            with self.assertRaisesRegex(ValueError, "SKU coverage"):
                validate(bundle, report, directory)

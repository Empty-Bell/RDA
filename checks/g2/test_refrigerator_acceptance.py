from pathlib import Path
import json
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_dashboard_build import build  # noqa: E402
from g2_refrigerator_acceptance import phase_readiness, validate, validate_artifact  # noqa: E402
from g2_refrigerator_control_summary import add_control_summary, build_summary  # noqa: E402


class RefrigeratorAcceptanceTests(unittest.TestCase):
    def inputs(self):
        bundle = {"manifest": {"run_id": "run-1", "runner": "ubuntu-24.04", "assessment_enabled": False}, "products": [{"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}]}
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
        self.assertEqual(result["phase_readiness"]["status"], "BLOCKED")
        self.assertIn("CANONICAL_ASSESSMENT_DISABLED", result["phase_readiness"]["gaps"])

    def test_phase_readiness_requires_complete_domain_and_model_coverage(self):
        bundle, report = self.inputs()
        bundle["manifest"].update({"overall_execution_status": "SUCCESS", "assessment_enabled": True})
        report["assessment_enabled"] = True
        bundle["assessments"] = [
            {"exact_sku": sku, "regulatory_domain": domain, "control_id": control,
             "assessment_status": "FINDING" if sku == "SKU-A" and control == "ENERGY_STAR_PUBLICATION" else "NO_EXCEPTION_OBSERVED",
             "issue_code": "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE" if sku == "SKU-A" and control == "ENERGY_STAR_PUBLICATION" else None,
             "severity": "HIGH" if sku == "SKU-A" and control == "ENERGY_STAR_PUBLICATION" else None}
            for sku in ("SKU-A", "SKU-B")
            for domain, control in (("EPA", "ENERGY_STAR_PUBLICATION"), ("FTC", "ENERGYGUIDE_NUMERIC"), ("FTC", "ENERGYGUIDE_MODEL_PREFIX"))
        ]
        next(item for item in bundle["assessments"] if item["exact_sku"] == "SKU-B" and item["control_id"] == "ENERGYGUIDE_NUMERIC").update(
            assessment_status="FINDING", issue_code="PDP_ANNUAL_ENERGY_MISSING", severity="LOW")
        report["energyguide_model_pattern"]["records"] = [
            {"exact_sku": sku, "display_outcome": "PASS"} for sku in ("SKU-A", "SKU-B")
        ]
        self.assertEqual(phase_readiness(bundle, report)["status"], "READY_FOR_FORMAL_REVIEW")
        bundle["assessments"][1]["assessment_status"] = "NOT_EVALUATED"
        self.assertIn("CANONICAL_ENERGYGUIDE_NUMERIC_INCOMPLETE", phase_readiness(bundle, report)["gaps"])
        bundle["assessments"][0]["assessment_status"] = "NO_EXCEPTION_OBSERVED"
        report["energyguide_model_pattern"]["records"].pop()
        self.assertIn("ENERGYGUIDE_MODEL_ASSESSMENT_INCOMPLETE", phase_readiness(bundle, report)["gaps"])

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

    def test_validates_a_saved_run_artifact_without_recollecting_sources(self):
        bundle, report = self.inputs()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_root = root / "runtime/g2/run-1"
            run_root.mkdir(parents=True)
            (run_root / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
            (run_root / "report.json").write_text(json.dumps(report), encoding="utf-8")
            build(bundle, report, run_root / "site")
            archive = root / "source.zip"
            with zipfile.ZipFile(archive, "w") as output:
                for path in (root / "runtime").rglob("*"):
                    if path.is_file():
                        output.write(path, path.relative_to(root / "runtime").as_posix())
            result = validate_artifact(archive, root / "extracted")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["run_id"], "run-1")

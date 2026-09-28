"""Failure-injection contracts for the unified execution and publication gates."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from publication_bundle import create, verify
from unified_run_gate import FAMILIES, build


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class OperationsTest(unittest.TestCase):
    def fixture(self, root):
        for family in FAMILIES:
            sku = f"{family.upper()}1"
            assessment = root / "unified" / family / "assessment" / "assessment.json"
            save(assessment, {"contract": "ASSESSMENT_TEST", "status": "PASS",
                              "sku_count": 1, "records": [{"exact_sku": sku, "grade": "PASS"}]})
            save(root / "unified" / family / "unified-family-manifest.json",
                 {"contract": "RDA_UNIFIED_FAMILY_EXECUTION_V1", "family": family,
                  "run_id": "run-a", "assessment_path": f"runtime/unified/{family}/assessment/assessment.json",
                  "assessment_sha256": hashlib.sha256(assessment.read_bytes()).hexdigest(),
                  "sku_count": 1, "counts": {"PASS": 1, "HIGH": 0, "MEDIUM": 0, "LOW": 0}})
            if family == "refrigerator":
                save(root / "g2" / "test" / "checkpoint.json",
                     {"status": "PASS", "github_run_id": "run-a"})
            else:
                for source in (("computer", "chromebook") if family == "computer" else (family,)):
                    save(root / "source-recon" / source / "recon.json", {"run_id": "run-a"})

    def test_complete_and_missing_artifact_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            self.assertEqual(build(root, "run-a", root / "out"), 0)
            self.assertEqual(json.loads((root / "out/unified-report.json").read_text())["model_count"], 11)
            (root / "unified/dishwasher/assessment/assessment.json").unlink()
            self.assertEqual(build(root, "run-a", root / "missing"), 1)
            result = json.loads((root / "missing/unified-report.json").read_text())
            self.assertEqual(result["execution_status"], "FAIL")
            self.assertIn("ASSESSMENT_MISSING:dishwasher", result["integrity_errors"])

    def test_failed_or_mixed_source_cannot_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            save(root / "source-recon/tv/recon.json", {"run_id": "old-run"})
            self.assertEqual(build(root, "run-a", root / "mixed"), 1)
            self.assertIn("SOURCE_RECON_IDENTITY_DIFFERS:tv",
                          json.loads((root / "mixed/unified-report.json").read_text())["integrity_errors"])
            save(root / "source-recon/tv/recon.json", {"run_id": "run-a"})
            report = root / "unified/tv/assessment/assessment.json"
            data = json.loads(report.read_text())
            data["status"] = "FAIL"
            save(report, data)
            self.assertEqual(build(root, "run-a", root / "failed"), 1)
            self.assertIn("ASSESSMENT_INCOMPLETE:tv",
                          json.loads((root / "failed/unified-report.json").read_text())["integrity_errors"])

    def test_publication_tampering_and_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp)
            for name in ("index.html", "app.js", "styles.css", "report-data.csv",
                         "report-all-fields.csv", "report-data.xlsx"):
                (docs / name).write_text("original", encoding="utf-8")
            save(docs / "model-data.json", {"run_number": 21, "records": [
                {"family": "TV", "model": "M1", "evidence_url": "./evidence/M1.json"}]})
            save(docs / "history.json", {"validated_runs": [{"run_id": "run-a", "run_number": 21}]})
            save(docs / "integration-manifest.json", {"unified_source_run_id": "run-a"})
            save(docs / "evidence/M1.json", {"family": "TV", "model": "M1"})
            create(docs, "run-a", "git-a")
            self.assertEqual(verify(docs, "run-a", "git-a")["model_count"], 1)
            snapshot = json.loads((docs / "model-data.json").read_text(encoding="utf-8"))
            snapshot["records"].append({"family": "Dryer", "model": "M1",
                                        "evidence_url": "./evidence/M1.json"})
            save(docs / "model-data.json", snapshot)
            with self.assertRaisesRegex(ValueError, "reused"):
                create(docs, "run-a", "git-a")
            snapshot["records"].pop()
            save(docs / "model-data.json", snapshot)
            with self.assertRaisesRegex(ValueError, "validated source run"):
                verify(docs, "run-b", "git-a")
            (docs / "app.js").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                verify(docs, "run-a", "git-a")
            (docs / "app.js").write_text("original", encoding="utf-8")
            self.assertEqual(verify(docs, "run-a", "git-a")["model_count"], 1)


if __name__ == "__main__":
    unittest.main()

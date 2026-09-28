"""Failure-injection contracts for the unified execution and publication gates."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from publication_bundle import LEGACY_CONTRACT, create, inspect, verify
from unified_family_run import main as run_family
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
            (root / "unified/dishwasher/unified-family-manifest.json").unlink()
            self.assertEqual(build(root, "run-a", root / "upload-failed"), 1)
            self.assertIn("FAMILY_MANIFEST_MISSING:dishwasher",
                          json.loads((root / "upload-failed/unified-report.json").read_text())["integrity_errors"])

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

    def test_live_stage_failures_never_emit_a_family_manifest(self):
        for family, failure, failed_stage in (("tv", "HTTP 429", "source_and_collection"),
                                              ("tv", "OCR crash", "assess_washer_or_tv"),
                                              ("monitor", "EPA timeout", "assess_epa")):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                with patch.dict("os.environ", {"GITHUB_RUN_ID": "123"}), patch(
                        "unified_family_run.source_and_collection", return_value=Path(temp)), patch(
                        "unified_family_run." + failed_stage, side_effect=RuntimeError(failure)):
                    with self.assertRaisesRegex(RuntimeError, failure):
                        run_family(family, Path(temp))
                self.assertFalse((Path(temp) / family / "unified-family-manifest.json").exists())

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

    def test_publication_text_hash_is_cross_platform_and_legacy_readable(self):
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp)
            for name in ("index.html", "app.js", "styles.css", "report-data.csv",
                         "report-all-fields.csv", "report-data.xlsx"):
                (docs / name).write_bytes(b"a\nb\n")
            save(docs / "model-data.json", {"run_number": 1, "records": []})
            save(docs / "history.json", {"validated_runs": [{"run_id": "r1", "run_number": 1}]})
            save(docs / "integration-manifest.json", {"unified_source_run_id": "r1"})
            create(docs, "r1", "sha")
            (docs / "app.js").write_bytes(b"a\r\nb\r\n")
            verify(docs, "r1", "sha")
            (docs / "app.js").write_bytes(b"a\nb\n")
            legacy = inspect(docs, "r1", "sha", LEGACY_CONTRACT)
            save(docs / "publication-manifest.json", legacy)
            verify(docs, "r1", "sha")
            (docs / "app.js").write_bytes(b"a\r\nb\r\n")
            with self.assertRaisesRegex(ValueError, "hash"):
                verify(docs, "r1", "sha")


if __name__ == "__main__":
    unittest.main()

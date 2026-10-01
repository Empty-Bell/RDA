import json
from pathlib import Path
import tempfile
import unittest

from select_unified_artifact import select


class SelectUnifiedArtifactTest(unittest.TestCase):
    def test_gate_uses_latest_passing_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for attempt, status in ((1, "PASS"), (2, "FAILED")):
                directory = root / f"unified-full-audit-report-123-{attempt}"
                directory.mkdir()
                (directory / "unified-report.json").write_text(json.dumps({
                    "run_id": "123", "execution_status": status,
                    "single_source_run": True,
                }), encoding="utf-8")
            self.assertEqual(select(root, "gate", "123", root / "out"), 1)

    def test_site_requires_same_source_sha(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for attempt, sha in ((1, "good"), (2, "other")):
                directory = root / f"validated-site-123-{attempt}"
                directory.mkdir()
                (directory / "publication-manifest.json").write_text(json.dumps({
                    "run_id": "123", "source_git_sha": sha,
                }), encoding="utf-8")
            self.assertEqual(select(root, "site", "123", root / "out", "good"), 1)


if __name__ == "__main__":
    unittest.main()

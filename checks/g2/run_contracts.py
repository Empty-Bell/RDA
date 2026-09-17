"""Write a small, inspectable report for the offline G2 normalization contracts."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> int:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite(
        loader.discover(str(ROOT / "checks/g2"), pattern=pattern)
        for pattern in ("test_normalized_pdp.py", "test_label_plan.py")
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "status": "PASS" if result.wasSuccessful() and not result.skipped else "FAILED",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "git_sha": os.getenv("GITHUB_SHA"),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    output = ROOT / "runtime/g2-contracts"
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g3_dishwasher_report_dashboard import build  # noqa: E402


class DishwasherDashboardTests(unittest.TestCase):
    def test_builds_consistent_action_queue_and_full_sku_report(self):
        def row(sku, outcome, findings, model):
            return {"exact_sku": sku, "display_outcome": outcome, "findings": findings, "controls": {"energy_star_publication": {"outcome": "PASS"}, "energyguide_numeric": {"comparisons": {"pdp_vs_energyguide_energy": "EQUAL", "energyguide_vs_epa_energy": "EQUAL"}}, "energyguide_model": {"comparisons": model}}}
        report = {"contract": "G3_DISHWASHER_CANONICAL_REPORT_V1", "status": "PASS", "sku_count": 2, "finding_count": 1, "rows": [row("SKU-A", "HIGH", [{"control": "MODEL_IDENTITY", "severity": "HIGH", "issue_code": "MODEL_IDENTITY_MISMATCH"}], {"pdp_vs_energyguide_model": "DIFFERENT", "pdp_vs_epa_model": "EQUAL", "energyguide_vs_epa_model": "DIFFERENT"}), row("SKU-B", "PASS", [], {"pdp_vs_energyguide_model": "EQUAL", "pdp_vs_epa_model": "EQUAL", "energyguide_vs_epa_model": "EQUAL"})]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "report.json"; source.write_text(json.dumps(report))
            build(source, root / "site")
            summary = json.loads((root / "site/data/summary.json").read_text())
            rows = json.loads((root / "site/data/report-data.json").read_text())
            findings = json.loads((root / "site/data/findings.json").read_text())
        self.assertEqual(summary["verdicts"], {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "PASS": 1})
        self.assertEqual(len(rows), 2); self.assertEqual(len(findings), 1)


if __name__ == "__main__":
    unittest.main()

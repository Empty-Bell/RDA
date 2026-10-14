import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.g3_dishwasher_comparison_package import build as build_package
from scripts.g3_dishwasher_source_match import build as build_match


class DishwasherUnreadablePopulationTests(unittest.TestCase):
    def test_unreadable_label_sku_stays_in_match_and_comparison_population(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pdp = root / "pdp"
            obs = root / "observation"
            epa = root / "epa"
            match = root / "match"
            package = root / "package"
            for path in (pdp / "pdp" / "DW70H83YETRAA", obs, epa):
                path.mkdir(parents=True, exist_ok=True)

            products = [{"exact_sku": "DW70H83YETRAA"}]
            (pdp / "products.json").write_text(json.dumps(products), encoding="utf-8")
            (pdp / "pdp" / "DW70H83YETRAA" / "result.json").write_text(json.dumps({
                "exact_sku": "DW70H83YETRAA",
                "status": "VERIFIED_EXACT_IDENTITY",
                "pdp_facts_raw": {"energy_consumption_raw": []},
            }), encoding="utf-8")

            index = {
                "sku_documents": [],
                "unreadable_documents": [{
                    "exact_sku": "DW70H83YETRAA",
                    "source_document_index": 0,
                    "url": "https://images.samsung.com/is/content/samsung/example.pdf",
                    "state": "NOT_ACCESSIBLE",
                    "severity": "HIGH",
                    "issue_code": "ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE",
                    "reason": "DECLARED_ENERGYGUIDE_RESPONSE_IS_NOT_A_PDF",
                }],
            }
            (obs / "sku-document-index.json").write_text(json.dumps(index), encoding="utf-8")
            rows = []
            (epa / "samsung-current-rows.json").write_text(json.dumps(rows), encoding="utf-8")

            build_match(obs, epa, match)
            match_report = json.loads((match / "match-report.json").read_text())
            self.assertEqual(match_report["sku_count"], 1)
            self.assertEqual(match_report["rows"][0]["exact_sku"], "DW70H83YETRAA")

            visual = root / "visual.json"
            visual.write_text(json.dumps({
                "contract": "G3_DISHWASHER_US_ENERGYGUIDE_VISUAL_REVIEW_V1",
                "status": "APPROVED",
                "reviews": [],
            }), encoding="utf-8")
            build_package(pdp, obs, epa, match, package, visual)
            report = json.loads((package / "comparison-package.json").read_text())
            self.assertEqual(report["sku_count"], 1)
            self.assertEqual(report["rows"][0]["exact_sku"], "DW70H83YETRAA")
            self.assertEqual(
                report["rows"][0]["energyguide_document_findings"][0]["issue_code"],
                "ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE",
            )


if __name__ == "__main__":
    unittest.main()

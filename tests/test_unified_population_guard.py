import json
from pathlib import Path
import tempfile
import unittest

from unified_pages_refresh import reconcile_plp_population, source_pdp_results


class UnifiedPopulationGuardTests(unittest.TestCase):
    def test_refrigerator_expansion_finds_same_run_g2_pdp(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "unified"
            pdp = source.parent / "g2" / "session" / "pdp-samples" / "0"
            pdp.mkdir(parents=True)
            (pdp / "result.json").write_text(json.dumps({
                "exact_sku": "RF-NEW", "status": "VERIFIED_EXACT_IDENTITY",
                "final_url": "https://www.samsung.com/us/refrigerators/model-sku-rf-new/",
            }), encoding="utf-8")
            (source.parent / "g2" / "session" / "bundle.json").write_text(json.dumps({
                "products": [{"exact_sku": "RF-NEW", "listings": [{
                    "pdp_url": "https://www.samsung.com/us/refrigerators/model-sku-rf-new/"
                }]}]
            }), encoding="utf-8")
            self.assertIn("RF-NEW", source_pdp_results(source, "refrigerator", {"RF-NEW"}))

    def test_refrigerator_bundle_listing_fills_unexported_pdp_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "unified"
            bundle = source.parent / "g2" / "session" / "bundle.json"
            bundle.parent.mkdir(parents=True)
            bundle.write_text(json.dumps({"products": [{
                "exact_sku": "RF-NEW", "listings": [{
                    "pdp_url": "https://www.samsung.com/us/refrigerators/model-sku-rf-new/"
                }]
            }]}), encoding="utf-8")
            result = source_pdp_results(source, "refrigerator", {"RF-NEW"})["RF-NEW"]
            self.assertEqual(result["status"], "SOURCE_LISTED_PDP_CAPTURE_NOT_EXPORTED")

    def test_large_source_drop_blocks_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            docs, source = root / "docs", root / "source"
            docs.mkdir()
            (docs / "model-data.json").write_text(json.dumps({
                "records": [{"family": "냉장고", "model": f"RF{i}"} for i in range(20)]
            }), encoding="utf-8")
            refrigerator = source / "refrigerator"
            refrigerator.mkdir(parents=True)
            (refrigerator / "unified-family-manifest.json").write_text(json.dumps({
                "family": "refrigerator", "run_id": "123", "sku_count": 10,
                "assessment_path": "runtime/unified/refrigerator/assessment/report.json",
            }), encoding="utf-8")
            (refrigerator / "assessment").mkdir()
            (refrigerator / "assessment/report.json").write_text(json.dumps({
                "records": [{"exact_sku": f"RF{i}"} for i in range(10)]
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "population dropped"):
                reconcile_plp_population(docs, source, {"run_id": "123"})


if __name__ == "__main__":
    unittest.main()

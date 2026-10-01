import json
from pathlib import Path
import tempfile
import unittest

from unified_pages_refresh import reconcile_plp_population


class UnifiedPopulationGuardTests(unittest.TestCase):
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

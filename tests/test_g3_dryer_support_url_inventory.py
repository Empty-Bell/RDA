"""Offline tests for PDP Support URL inspection."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.g3_dryer_support_url_inventory import inventory


class DryerSupportUrlInventoryTest(unittest.TestCase):
    def test_inventory_detects_energyguide_like_url_under_alternate_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdp = root / "pdp" / "DV1"
            pdp.mkdir(parents=True)
            (root / "collection-summary.json").write_text(json.dumps({
                "status": "PASS", "collection_run_id": "123",
                "coverage": {"population_count": 1}}), encoding="utf-8")
            result = {
                "exact_sku": "DV1", "status": "VERIFIED_EXACT_IDENTITY",
                "pdp_facts_raw": {"support_documents_raw": [
                    {"name": "Product Information Sheet", "type": "PDF",
                     "url": "https://images.samsung.com/p6pim/us/energyguide/dv1.pdf"},
                    {"name": "Warranty", "type": "PDF",
                     "url": "https://images.samsung.com/p6pim/us/warranty/dv1.pdf"}]}}
            (pdp / "result.json").write_text(json.dumps(result), encoding="utf-8")
            report = inventory(root, "123")
            self.assertEqual(report["energyguide_term_url_candidate_count"], 1)
            self.assertEqual(report["energyguide_term_url_candidates"][0]["name_raw"],
                             "Product Information Sheet")
            self.assertEqual(report["support_document_name_inventory"][1]["name_raw"],
                             "Warranty")


if __name__ == "__main__":
    unittest.main()

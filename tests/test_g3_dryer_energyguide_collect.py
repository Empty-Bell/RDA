"""Dryer Support inventory must distinguish canonical labels from all documents."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.g3_dryer_energyguide_collect import load_documents


class DryerSupportInventoryContract(unittest.TestCase):
    def test_noncanonical_support_entries_are_visible_without_becoming_label_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdp = root / "pdp" / "DV1"
            pdp.mkdir(parents=True)
            (root / "collection-summary.json").write_text(json.dumps({
                "status": "PASS", "collection_run_id": "123",
                "coverage": {"population_count": 1}}), encoding="utf-8")
            result = {
                "exact_sku": "DV1", "status": "VERIFIED_EXACT_IDENTITY",
                "browser_identity": {"user_agent": "Chrome/123"},
                "pdp_facts_raw": {
                    "energyguide_documents": [],
                    "support_documents_raw": [
                        {"name": "Product Information Sheet", "type": "PDF",
                         "url": "https://images.samsung.com/energyguide/dv1.pdf"},
                        {"name": "Manual", "type": "PDF",
                         "url": "https://images.samsung.com/manual/dv1.pdf"}]}}
            (pdp / "result.json").write_text(json.dumps(result), encoding="utf-8")
            declarations, _, coverage, names = load_documents(root, "123")
            self.assertEqual(declarations, [])
            self.assertEqual(coverage[0]["support_document_count"], 0)
            self.assertEqual(coverage[0]["all_support_document_count"], 2)
            self.assertEqual(coverage[0]["state"], "NO_CANONICAL_ENERGYGUIDE_DECLARED")
            self.assertEqual([row["name_raw"] for row in names],
                             ["Manual", "Product Information Sheet"])


if __name__ == "__main__":
    unittest.main()

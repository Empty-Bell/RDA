"""Contracts for the bounded PDP-link probe target selection."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.g3_dryer_pdp_link_probe import TARGET_SKUS, load_targets


class DryerPdpLinkProbeTest(unittest.TestCase):
    def test_uses_only_verified_skus_without_canonical_energyguide(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "collection-summary.json").write_text(json.dumps({
                "status": "PASS", "collection_run_id": "123",
                "coverage": {"population_count": len(TARGET_SKUS)}}), encoding="utf-8")
            results_dir = root / "pdp"
            results_dir.mkdir()
            products = []
            for index, sku in enumerate(TARGET_SKUS):
                folder = results_dir / str(index)
                folder.mkdir()
                (folder / "result.json").write_text(json.dumps({
                    "exact_sku": sku, "status": "VERIFIED_EXACT_IDENTITY",
                    "pdp_facts_raw": {"energyguide_documents": []}}), encoding="utf-8")
                products.append({"exact_sku": sku, "listings": [{
                    "pdp_url": f"https://www.samsung.com/us/product-sku-{sku.lower().replace('/', '-')}/"}]})
            (root / "products.json").write_text(json.dumps(products), encoding="utf-8")
            targets = load_targets(root, "123")
            self.assertEqual([row["exact_sku"] for row in targets], list(TARGET_SKUS))
            self.assertTrue(all(row["pdp_url"].startswith("https://www.samsung.com/") for row in targets))

    def test_refuses_sku_with_canonical_energyguide_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "collection-summary.json").write_text(json.dumps({
                "status": "PASS", "collection_run_id": "123",
                "coverage": {"population_count": 1}}), encoding="utf-8")
            (root / "pdp").mkdir()
            (root / "products.json").write_text(json.dumps([{
                "exact_sku": TARGET_SKUS[0], "listings": [{
                    "pdp_url": "https://www.samsung.com/us/product-sku-dv90f53aesa3/"}]}]), encoding="utf-8")
            folder = root / "pdp" / "0"
            folder.mkdir()
            (folder / "result.json").write_text(json.dumps({
                "exact_sku": TARGET_SKUS[0], "status": "VERIFIED_EXACT_IDENTITY",
                "pdp_facts_raw": {"energyguide_documents": [{"url": "https://example.test/guide.pdf"}]}}),
                encoding="utf-8")
            with self.assertRaises(ValueError):
                load_targets(root, "123", [TARGET_SKUS[0]])


if __name__ == "__main__":
    unittest.main()

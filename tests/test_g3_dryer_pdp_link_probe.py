"""Contracts for the bounded PDP-link probe target selection."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.g3_dryer_pdp_link_probe import SAMPLE_SKUS, load_targets


class DryerPdpLinkProbeTest(unittest.TestCase):
    def test_uses_only_verified_skus_without_canonical_energyguide(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "collection-summary.json").write_text(json.dumps({
                "status": "PASS", "collection_run_id": "123",
                "coverage": {"population_count": len(SAMPLE_SKUS)}}), encoding="utf-8")
            results_dir = root / "pdp"
            results_dir.mkdir()
            products = []
            for index, sku in enumerate(SAMPLE_SKUS):
                folder = results_dir / str(index)
                folder.mkdir()
                (folder / "result.json").write_text(json.dumps({
                    "exact_sku": sku, "status": "VERIFIED_EXACT_IDENTITY",
                    "pdp_facts_raw": {"energyguide_documents": []}}), encoding="utf-8")
                products.append({"exact_sku": sku, "listings": [{
                    "pdp_url": f"https://www.samsung.com/us/product-sku-{sku.lower().replace('/', '-')}/"}]})
            (root / "products.json").write_text(json.dumps(products), encoding="utf-8")
            targets = load_targets(root, "123", SAMPLE_SKUS)
            self.assertEqual([row["exact_sku"] for row in targets], list(SAMPLE_SKUS))
            self.assertTrue(all(row["pdp_url"].startswith("https://www.samsung.com/") for row in targets))

    def test_refuses_sku_with_canonical_energyguide_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "collection-summary.json").write_text(json.dumps({
                "status": "PASS", "collection_run_id": "123",
                "coverage": {"population_count": 1}}), encoding="utf-8")
            (root / "pdp").mkdir()
            (root / "products.json").write_text(json.dumps([{
                "exact_sku": SAMPLE_SKUS[0], "listings": [{
                    "pdp_url": "https://www.samsung.com/us/product-sku-dv90f53aesa3/"}]}]), encoding="utf-8")
            folder = root / "pdp" / "0"
            folder.mkdir()
            (folder / "result.json").write_text(json.dumps({
                "exact_sku": SAMPLE_SKUS[0], "status": "VERIFIED_EXACT_IDENTITY",
                "pdp_facts_raw": {"energyguide_documents": [{"url": "https://example.test/guide.pdf"}]}}),
                encoding="utf-8")
            with self.assertRaises(ValueError):
                load_targets(root, "123", [SAMPLE_SKUS[0]])

    def test_full_targets_are_partitioned_without_overlap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skus = [f"DVTEST{index:03d}" for index in range(7)]
            (root / "collection-summary.json").write_text(json.dumps({
                "status": "PASS", "collection_run_id": "123",
                "coverage": {"population_count": len(skus)}}), encoding="utf-8")
            results_dir = root / "pdp"
            results_dir.mkdir()
            products = []
            for index, sku in enumerate(skus):
                folder = results_dir / str(index)
                folder.mkdir()
                (folder / "result.json").write_text(json.dumps({
                    "exact_sku": sku, "status": "VERIFIED_EXACT_IDENTITY",
                    "pdp_facts_raw": {"energyguide_documents": []}}), encoding="utf-8")
                products.append({"exact_sku": sku, "listings": [{
                    "pdp_url": f"https://www.samsung.com/us/product-{sku.lower()}/"}]})
            (root / "products.json").write_text(json.dumps(products), encoding="utf-8")
            targets = load_targets(root, "123")
            shards = [[row for index, row in enumerate(targets) if index % 3 == shard]
                      for shard in range(3)]
            flattened = [row["exact_sku"] for shard in shards for row in shard]
            self.assertEqual(sorted(flattened), skus)
            self.assertEqual(len(flattened), len(set(flattened)))
            self.assertEqual([len(shard) for shard in shards], [3, 2, 2])


if __name__ == "__main__":
    unittest.main()

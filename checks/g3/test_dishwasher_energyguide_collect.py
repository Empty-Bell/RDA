import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from g3_dishwasher_energyguide_collect import collect_documents, load_verified_documents  # noqa: E402


class DishwasherEnergyGuideCollectionTests(unittest.TestCase):
    def collection(self, root: Path):
        sku = "DW80B7070US/AA"
        result = {"exact_sku": sku, "status": "VERIFIED_EXACT_IDENTITY",
                  "browser_identity": {"user_agent": "Mozilla/5.0 Chrome/140.0.0.0 Safari/537.36"},
                  "pdp_facts_raw": {"energyguide_documents": [{"name": "Energy Guide", "type": "PDF", "url": "https://images.samsung.test/guide.pdf"}]}}
        folder = root / "pdp" / "DW80B7070US%2FAA"
        folder.mkdir(parents=True)
        (folder / "result.json").write_text(json.dumps(result), encoding="utf-8")
        (root / "collection-summary.json").write_text(json.dumps({"status": "PASS", "collection_run_id": "collection-1", "coverage": {"population_count": 1}}), encoding="utf-8")

    def test_hashes_one_pdf_and_reuses_one_url_for_multiple_skus(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "collection"
            self.collection(root)
            declarations, identity = load_verified_documents(root, "collection-1")
            copied = {**declarations[0], "exact_sku": "DW90F89P0USRAA"}
            data = b"%PDF-1.7 synthetic label"
            result = collect_documents(declarations + [copied], Path(directory) / "out", identity,
                                       fetch=lambda url, ua: (data, url, "application/pdf", 200))
        self.assertEqual(result["url_count"], 1)
        self.assertEqual(result["pdf_hash_count"], 1)
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(result["records"][0]["retrieval"]["sha256"], hashlib.sha256(data).hexdigest())

    def test_invalid_pdf_is_recorded_as_a_failure(self):
        declaration = {"exact_sku": "DW90F89P0USRAA", "source_document_index": 0, "name_raw": "Energy Guide", "type_raw": "PDF", "url": "https://images.samsung.test/guide.pdf"}
        with tempfile.TemporaryDirectory() as directory:
            result = collect_documents([declaration], directory, "Mozilla Chrome/140.0.0.0",
                                       fetch=lambda url, ua: (b"<html>blocked</html>", url, "text/html", 200))
        self.assertEqual(result["failed_url_count"], 1)
        self.assertEqual(result["records"][0]["retrieval"]["status"], "FAILED")

    def test_rejects_incomplete_collection_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.collection(root)
            summary = json.loads((root / "collection-summary.json").read_text())
            summary["coverage"]["population_count"] = 2
            (root / "collection-summary.json").write_text(json.dumps(summary), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "full PDP evidence"):
                load_verified_documents(root, "collection-1")

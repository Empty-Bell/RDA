from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from g3_dishwasher_collect import coverage, load_population, verify_identity  # noqa: E402
from source_contract import project_bridge  # noqa: E402


class DishwasherCollectionTests(unittest.TestCase):
    def fixture_recon(self, root: Path):
        page = ROOT / "tests/fixtures/dishwasher/pf-page-0.json"
        target = root / "fixtures/pf-page-0.json"
        target.parent.mkdir(parents=True)
        target.write_bytes(page.read_bytes())
        recon = {"status": "PASS", "run_id": "source-1", "scope": "dishwasher source contracts only",
                 "observations": [{"request_body": {"startIndex": 0}, "fixture": "fixtures/pf-page-0.json",
                                   "fixture_sha256": hashlib.sha256(target.read_bytes()).hexdigest()}]}
        (root / "recon.json").write_text(json.dumps(recon), encoding="utf-8")

    def test_builds_exact_population_from_hash_bound_pf_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture_recon(root)
            products, summary = load_population(root, "source-1")
        self.assertEqual(summary["total_groups"], 9)
        self.assertEqual(len(products), 21)
        self.assertTrue(all(product["listings"][0]["product_group"] == "dishwasher" for product in products))

    def test_rejects_tampered_pf_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture_recon(root)
            (root / "fixtures/pf-page-0.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                load_population(root, "source-1")

    def test_identity_binds_url_jsonld_and_exact_bridge_sku(self):
        sku = "DW90F89P0USRAA"
        bridge = project_bridge(json.loads((ROOT / "tests/fixtures/dishwasher/bridge-specs-support.json").read_text(encoding="utf-8")))
        snapshot = {"jsonld_parse_errors": 0, "product_jsonld": [{"sku": sku, "mpn": sku}]}
        facts = verify_identity(sku, f"https://www.samsung.com/us/dishwashers/model-sku-{sku.lower()}", snapshot, bridge)
        self.assertEqual(facts["energy_consumption_raw"][0]["value"], "225")
        self.assertEqual(facts["capacity_raw"][0]["value"], "16")
        with self.assertRaisesRegex(ValueError, "another exact SKU"):
            verify_identity(sku, "https://www.samsung.com/us/dishwashers/model-sku-other", snapshot, bridge)

    def test_coverage_keeps_failed_and_unattempted_distinct(self):
        products = [{"exact_sku": sku} for sku in ("A", "B", "C")]
        results = [{"exact_sku": "A", "status": "VERIFIED_EXACT_IDENTITY"}, {"exact_sku": "B", "status": "FAILED"}]
        result = coverage(products, results)
        self.assertEqual(result["counts"], {"VERIFIED_EXACT_IDENTITY": 1, "FAILED": 1, "NOT_ATTEMPTED": 1})

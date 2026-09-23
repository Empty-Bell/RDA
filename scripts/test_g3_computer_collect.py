import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.g3_computer_collect import load_population, shard_for

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "computer"


def write_leg(root, family, fixture_name, run_id):
    root.mkdir(parents=True)
    page_name = "pf-page-0.json" if family == "computer" else "pf-chromebook-page-0.json"
    raw = (FIXTURES / page_name).read_bytes()
    (root / "pf.json").write_bytes(raw)
    report = {"status": "PASS", "run_id": run_id,
        "scope": f"{family} source contracts only", "checks": [{"status": "PASS"}],
        "observations": [{"request_body": {"startIndex": 0}, "fixture": "pf.json",
            "fixture_sha256": hashlib.sha256(raw).hexdigest()}]}
    (root / "recon.json").write_text(json.dumps(report), encoding="utf-8")


class ComputerCollectionPopulationTests(unittest.TestCase):
    def test_union_is_exactly_23_galaxy_books_plus_one_chromebook(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_leg(root / "computer", "computer", "", "123")
            write_leg(root / "chromebook", "chromebook", "", "123")
            products, summary = load_population(root / "computer", root / "chromebook", "123")
        self.assertEqual(len(products), 24)
        self.assertEqual(len({row["exact_sku"] for row in products}), 24)
        self.assertEqual(summary["unique_exact_skus"], 24)
        self.assertEqual({row["source_leg"] for row in products}, {"computer", "chromebook"})

    def test_shards_are_disjoint_and_cover_the_population(self):
        skus = [f"SKU-{n}" for n in range(24)]
        shards = [[sku for sku in skus if shard_for(sku, 3) == index] for index in range(3)]
        self.assertEqual(set().union(*(set(shard) for shard in shards)), set(skus))
        self.assertEqual(sum(len(shard) for shard in shards), len(skus))
        self.assertTrue(all(shards))

    def test_source_artifact_run_identity_is_mandatory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_leg(root / "computer", "computer", "", "123")
            write_leg(root / "chromebook", "chromebook", "", "123")
            with self.assertRaisesRegex(ValueError, "requested successful run"):
                load_population(root / "computer", root / "chromebook", "999")


if __name__ == "__main__":
    unittest.main()


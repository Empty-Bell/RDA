import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.g3_computer_collect import load_population, shard_for
from scripts.claim_recon import DOM_SNAPSHOT

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "computer"


def write_leg(root, family, fixture_name, run_id):
    root.mkdir(parents=True)
    page_name = "pf-page-0.json" if family == "computer" else "pf-chromebook-page-0.json"
    raw = (FIXTURES / page_name).read_bytes()
    (root / "pf.json").write_bytes(raw)
    groups = json.loads(raw)["searchResults"]
    (root / "population-observation.json").write_text(json.dumps({
        "groups": len(groups),
        "rendered_tiles": [{"sku": group["modelCode"], "url": "https://www.samsung.com" + group["pdpURL"]}
            for group in groups],
        "rendered_tile_groups": [group["group_id"] for group in groups],
    }), encoding="utf-8")
    (root / "plp-claim-observation.json").write_text(json.dumps({
        "cards": [{"sku": group["modelCode"]} for group in groups]
    }), encoding="utf-8")
    report = {"status": "PASS", "run_id": run_id,
        "scope": f"{family} source contracts only", "checks": [{"status": "PASS"}],
        "observations": [{"request_body": {"startIndex": 0}, "fixture": "pf.json",
            "fixture_sha256": hashlib.sha256(raw).hexdigest()}]}
    (root / "recon.json").write_text(json.dumps(report), encoding="utf-8")


class ComputerCollectionPopulationTests(unittest.TestCase):
    def test_union_contains_only_rendered_plp_card_skus(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_leg(root / "computer", "computer", "", "123")
            write_leg(root / "chromebook", "chromebook", "", "123")
            products, summary = load_population(root / "computer", root / "chromebook", "123")
        self.assertEqual(len(products), 12)
        self.assertEqual(len({row["exact_sku"] for row in products}), 12)
        self.assertEqual(summary["unique_exact_skus"], 12)
        self.assertNotIn("NP740VJG-KA1US", {row["exact_sku"] for row in products})
        self.assertEqual(summary["source_legs"][0]["pf_variant_count"], 23)
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


class ComputerPdpSelectorContractTests(unittest.TestCase):
    def test_pdp_configurator_selectors_use_the_observed_root_id(self):
        self.assertIn("#pdp-page .q6b6RelationContainer", DOM_SNAPSHOT)
        self.assertNotIn(".pdp-page .q6b6RelationContainer", DOM_SNAPSHOT)


if __name__ == "__main__":
    unittest.main()


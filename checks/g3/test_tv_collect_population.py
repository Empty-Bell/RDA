"""TV collection population follows rendered PLP cards."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from g3_tv_collect import load_population  # noqa: E402
from source_contract import pf_population  # noqa: E402


class TelevisionPopulationTests(unittest.TestCase):
    def test_rendered_mna_card_is_included_and_hidden_variant_is_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pages = []
            for index in range(2):
                page = json.loads((ROOT / f"tests/fixtures/tv/pf-page-{index}.json").read_text(encoding="utf-8"))
                if index == 0:
                    variant = page["searchResults"][0]["groupedProductList"][1]
                    variant["modelCode"] = "MNA101MS1BCXZA"
                    variant["modelName"] = "MNA101MS1BC"
                    variant["id"] = "MNA101MS1BCXZA"
                    variant["pdpURL"] = "/us/tvs/micro-led/101-inch-micro-led-sku-mna101ms1bcxza"
                fixture = root / f"pf-page-{index}.json"
                fixture.write_text(json.dumps(page), encoding="utf-8")
                pages.append({"request_body": {"startIndex": index * 21},
                              "fixture": fixture.name,
                              "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest()})
            expected_source_count = pf_population([json.loads((root / f"pf-page-{i}.json").read_text(encoding="utf-8"))
                                                   for i in range(2)])["unique_exact_skus"]
            (root / "recon.json").write_text(json.dumps({"status": "PASS", "run_id": "source-1",
                "scope": "tv source contracts only", "observations": pages}), encoding="utf-8")
            groups = [group for index in range(2) for group in
                      json.loads((root / f"pf-page-{index}.json").read_text(encoding="utf-8"))["searchResults"]]
            (root / "population-observation.json").write_text(json.dumps({
                "groups": len(groups),
                "rendered_tiles": [{"sku": group["modelCode"], "url": group["pdpURL"]} for group in groups],
                "rendered_tile_groups": [group["group_id"] for group in groups],
            }), encoding="utf-8")
            (root / "plp-claim-observation.json").write_text(json.dumps({
                "cards": [{"sku": group["modelCode"]} for group in groups]
            }), encoding="utf-8")

            products, summary = load_population(root, "source-1")

        skus = {row["exact_sku"] for row in products}
        self.assertNotIn("MNA101MS1BCXZA", skus)
        self.assertIn("MNA89MS1BACXZA", skus)
        self.assertIn("MRN75R95HAFXZA", skus)
        self.assertEqual(summary["source_unique_exact_skus"], expected_source_count)
        self.assertEqual(summary["unique_exact_skus"], len(groups))
        self.assertEqual(summary["population_basis"], "EXACT_SKUS_ON_RENDERED_PLP_PRODUCT_CARDS")


if __name__ == "__main__":
    unittest.main()

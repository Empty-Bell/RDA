import json
from pathlib import Path
import tempfile
import unittest

from g3_computer_epa_candidates import COLLECTION_CONTRACT, build_candidates, load_collection
from g3_computer_energy_star_assessment import assess_record


class ComputerRedirectPipelineTests(unittest.TestCase):
    def test_confirmed_redirect_reaches_medium_assessment_with_stock_evidence(self):
        sku = "NP740VJG-KG2US"
        requested = "https://www.samsung.com/us/book-sku-np740vjg-kg2us"
        final = "https://www.samsung.com/us/book-sku-np960ujh-xg2us/"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(3):
                shard = root / f"shard-{index}"
                shard.mkdir()
                (shard / "shard-summary.json").write_text(json.dumps({
                    "contract": COLLECTION_CONTRACT, "status": "PASS",
                    "collection_run_id": "123", "source_run_id": "123",
                    "all_population_skus": [sku],
                    "assigned_skus": [sku] if index == 0 else [],
                }), encoding="utf-8")
            pdp = root / "shard-0" / "pdp" / sku
            pdp.mkdir(parents=True)
            (pdp / "result.json").write_text(json.dumps({
                "exact_sku": sku, "status": "PDP_REDIRECT_CONFIRMED",
                "requested_url": requested, "final_url": final,
                "source_claim_listing_raw": {"energyStarFlg": "Y", "stockFlag": "N"},
                "redirect_observations": [{"requested_url": requested, "final_url": final} for _ in range(3)],
            }), encoding="utf-8")
            skus, products, claims, facts, source_run = load_collection(root, "123")
            self.assertEqual(skus, [sku])
            output = root / "candidates"
            build_candidates(skus, products, claims, facts, [], source_run, {}, output)
            report = json.loads((output / "computer-epa-source-candidates.json").read_text())
            assessment = assess_record(report["records"][0])
            self.assertEqual(assessment["display_outcome"], "MEDIUM")
            self.assertEqual(assessment["findings"][0]["issue_code"], "PDP_LINK_WRONG_MODEL")
            self.assertEqual(assessment["pdp_identity_failure"]["plp_stock_flag_raw"], "N")


if __name__ == "__main__":
    unittest.main()

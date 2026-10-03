import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import g3_computer_collect as computer


class ComputerCollectRetryTest(unittest.TestCase):
    def test_three_same_wrong_model_redirects_become_actionable_routing_observation(self):
        sku = "NP740VJG-KG2US"
        requested = "https://www.samsung.com/us/computers/book-sku-np740vjg-kg2us"
        final = "https://www.samsung.com/us/computers/other-sku-np960ujh-xg2us/"
        product = {"exact_sku": sku, "listing": {"pdp_url": requested},
                   "source_claim_listing_raw": {"energyStarFlg": "Y"}}
        failure = {"exact_sku": sku, "status": "FAILED", "requested_url": requested,
                   "final_url": final, "failure_class": "SELECTED_SKU_DIFFERS_FROM_REQUESTED"}
        selection = {"selected_controls": [{"sku": "NP960UJH-XG2US"}],
                     "continue_sku": "NP960UJH-XG2US", "continue_visible": True}
        failure.update(initial_http_status=200, selected_configuration_raw=selection,
                       identity_observations=[{"url": final, "selection": selection}] * 4)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "pdp" / sku
            folder.mkdir(parents=True)
            with patch.object(computer, "collect", return_value=[failure.copy()]):
                rows = computer.retry_failed([product], [failure], root)
            self.assertEqual(rows[0]["status"], "PDP_REDIRECT_CONFIRMED")
            self.assertEqual(len(rows[0]["redirect_observations"]), 3)
            self.assertEqual(json.loads((folder / "result.json").read_text())["status"],
                             "PDP_REDIRECT_CONFIRMED")

    def test_unsettled_identity_is_not_accepted(self):
        sku = "NP740VJG-KG2US"
        selection = {"selected_controls": [{"sku": sku}],
                     "continue_sku": sku, "continue_visible": True}
        sample = {"url": "https://www.samsung.com/us/book-sku-np740vjg-kg2us/",
                  "selection": selection}
        self.assertFalse(computer.settled_identity([sample] * 3, sku))
        self.assertTrue(computer.settled_identity([sample] * 4, sku))
        self.assertFalse(computer.settled_identity([sample] * 3 + [
            {**sample, "selection": {**selection, "continue_sku": "OTHER"}}], sku))
        self.assertFalse(computer.settled_identity([sample] * 4, "NP740VJG-KA1US"))

    def test_wrong_default_gets_full_observation_window(self):
        from unittest.mock import Mock
        page = Mock(url="https://www.samsung.com/us/book-sku-other/")
        samples = []
        with patch.object(computer, "read_selection", return_value={}):
            computer.observe_identity(page, "NP740VJG-KG2US", samples)
        self.assertEqual(len(samples), 31)
        self.assertEqual(page.wait_for_timeout.call_count, 30)

    def test_changing_redirect_target_remains_collection_failure(self):
        sku = "NP740VJG-KG2US"
        requested = "https://www.samsung.com/us/computers/book-sku-np740vjg-kg2us"
        base = {"exact_sku": sku, "status": "FAILED", "requested_url": requested,
                "failure_class": "SELECTED_SKU_DIFFERS_FROM_REQUESTED"}
        product = {"exact_sku": sku, "listing": {"pdp_url": requested},
                   "source_claim_listing_raw": {"energyStarFlg": "Y"}}
        with tempfile.TemporaryDirectory() as temporary:
            first = {**base, "final_url": "https://www.samsung.com/us/book-sku-other1/"}
            next_rows = iter([{**base, "final_url": "https://www.samsung.com/us/book-sku-other2/"},
                              {**base, "final_url": "https://www.samsung.com/us/book-sku-other2/"}])
            with patch.object(computer, "collect", side_effect=lambda *_: [next(next_rows)]):
                rows = computer.retry_failed([product], [first], temporary)
            self.assertEqual(rows[0]["status"], "FAILED")

    def test_retries_only_failed_sku_and_promotes_exact_verified_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            failed_sku = "NP760XJG-KG2US"
            successful_sku = "NP740VJG-KG2US"
            original = root / "pdp" / failed_sku
            original.mkdir(parents=True)
            (original / "result.json").write_text('{"status":"FAILED"}')
            products = [{"exact_sku": failed_sku}, {"exact_sku": successful_sku}]
            rows = [{"exact_sku": failed_sku, "status": "FAILED"},
                    {"exact_sku": successful_sku, "status": "VERIFIED_EXACT_IDENTITY"}]
            called = []

            def recovered_capture(selected, destination):
                called.append([row["exact_sku"] for row in selected])
                folder = Path(destination) / "pdp" / failed_sku
                folder.mkdir(parents=True)
                for name in ("result.json", "snapshot.json", "specs.json"):
                    (folder / name).write_text(json.dumps({"exact_sku": failed_sku, "name": name}))
                return [{"exact_sku": failed_sku, "status": "VERIFIED_EXACT_IDENTITY"}]

            with patch.object(computer, "collect", recovered_capture):
                result = computer.retry_failed(products, rows, root)
            self.assertEqual(called, [[failed_sku]])
            self.assertEqual([row["status"] for row in result],
                             ["VERIFIED_EXACT_IDENTITY", "VERIFIED_EXACT_IDENTITY"])
            for name in ("result.json", "snapshot.json", "specs.json"):
                self.assertEqual(json.loads((original / name).read_text())["exact_sku"], failed_sku)


if __name__ == "__main__":
    unittest.main()

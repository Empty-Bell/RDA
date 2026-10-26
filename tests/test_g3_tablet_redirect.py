import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import g3_tablet_assessment as assessment
import g3_tablet_collect as collect
import g3_tablet_epa_candidates as candidates

SKU = "SM-X828UZAAATT"
REQUESTED = "https://www.samsung.com/us/tablets/galaxy-tab-s10/buy/galaxy-tab-s10-ultra-sku-sm-x828uzaaatt/"
FINAL = "https://www.samsung.com/us/tablets/galaxy-tab-s10/buy/galaxy-tab-s10-plus-sku-sm-x820nzaexar/"
LISTING = {"modelCode": SKU, "stockFlag": "N", "energyStarFlg": "Y"}


def selection(sku="sm-x820nzaexar"):
    return {"continue_sku": sku, "continue_visible": True, "selected_controls": []}


def failed(final=FINAL, sku="sm-x820nzaexar", status=200, samples=4):
    shown = selection(sku)
    return {"exact_sku": SKU, "status": "FAILED", "requested_url": REQUESTED, "final_url": final,
            "http_status": status, "failure_class": "SELECTED_SKU_DIFFERS_FROM_REQUESTED",
            "selection_observed_raw": shown,
            "identity_observations": [{"url": final, "selection": shown}] * samples}


PRODUCT = {"exact_sku": SKU, "source_claim_listing_raw": LISTING, "listing": {"pdp_url": REQUESTED}}


class RetryTests(unittest.TestCase):
    def run_retry(self, first, later):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pdp" / SKU).mkdir(parents=True)
            with patch.object(collect, "collect", side_effect=[[row] for row in later]):
                rows = collect.retry_failed([PRODUCT], [first], root)
            return rows[0], json.loads((root / "pdp" / SKU / "result.json").read_text()) \
                if (root / "pdp" / SKU / "result.json").exists() else None

    def test_three_settled_identical_wrong_model_attempts_are_a_redirect_finding(self):
        row, written = self.run_retry(failed(), [failed(), failed()])
        self.assertEqual(row["status"], "PDP_REDIRECT_CONFIRMED")
        self.assertEqual(len(row["redirect_observations"]), 3)
        self.assertEqual(row["redirect_destination_sku"], "sm-x820nzaexar")
        self.assertEqual(row["source_claim_listing_raw"], LISTING)
        self.assertEqual(written["status"], "PDP_REDIRECT_CONFIRMED")

    def test_unstable_or_inconsistent_attempts_stay_source_failures(self):
        other = "https://www.samsung.com/us/tablets/buy/galaxy-tab-a9-sku-sm-x110nzaaxar/"
        cases = {
            "different destination": [failed(), failed(other, "sm-x110nzaaxar")],
            "http error": [failed(), failed(status=503)],
            "unsettled samples": [failed(), failed(samples=3)],
            "other failure class": [failed(), {**failed(), "failure_class": "SOURCE_COLLECTION_FAILED"}],
            "destination is the requested sku": [failed(), failed(REQUESTED, SKU.lower())],
            "continue sku not the url sku": [failed(), failed(sku="sm-x999nzaaxar")],
        }
        for name, later in cases.items():
            with self.subTest(name):
                row, _ = self.run_retry(failed(), later)
                self.assertEqual(row["status"], "FAILED")

    def test_recovery_on_retry_keeps_initial_attempt_and_is_not_a_finding(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "pdp" / SKU
            original.mkdir(parents=True)
            (original / "result.json").write_text("{}")
            recovered = root / "retry-1" / "pdp" / SKU
            recovered.mkdir(parents=True)
            (recovered / "result.json").write_text('{"status": "VERIFIED_EXACT_IDENTITY"}')
            verified = {"exact_sku": SKU, "status": "VERIFIED_EXACT_IDENTITY"}
            with patch.object(collect, "collect", return_value=[verified]):
                rows = collect.retry_failed([PRODUCT], [failed()], root)
            self.assertEqual(rows[0]["status"], "VERIFIED_EXACT_IDENTITY")
            self.assertTrue((root / "initial-attempt" / "pdp" / SKU / "result.json").exists())
            self.assertIn("VERIFIED", (original / "result.json").read_text())


def redirect_result():
    row = {**failed(), "status": "PDP_REDIRECT_CONFIRMED", "source_claim_listing_raw": LISTING}
    row["redirect_observations"] = [{"requested_url": REQUESTED, "final_url": FINAL}] * 3
    return row


class CandidateTests(unittest.TestCase):
    def shard(self, root, result):
        folder = root / "shard-0"
        (folder / "pdp" / SKU).mkdir(parents=True)
        (folder / "pdp" / SKU / "result.json").write_text(json.dumps(result))
        (folder / "products.json").write_text(json.dumps([PRODUCT]))
        (folder / "shard-summary.json").write_text(json.dumps({
            "contract": "G3_TABLET_EXACT_SKU_PDP_V1", "status": "PASS", "collection_run_id": "7",
            "shard_count": 1, "shard_index": 0, "all_population_skus": [SKU],
            "assigned_skus": [SKU], "source_run_id": "5"}))

    def test_redirect_result_is_loaded_without_borrowing_destination_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            self.shard(Path(temp), redirect_result())
            skus, products, records, claims, facts, _ = candidates.load_collection(temp, "7")
            self.assertEqual(skus, [SKU])
            self.assertEqual(facts[SKU], {})
            self.assertEqual(claims[SKU], {"exact_sku": SKU, "plp_energy_star_flag_raw": "Y"})
            report = candidates.build_candidates(skus, products, records, claims, facts, [], "5",
                {"capture_run_id": "9"}, Path(temp) / "out")
            failure = report["records"][0]["pdp_identity_failure"]
            self.assertEqual((failure["requested_url"], failure["final_url"], failure["plp_stock_flag_raw"]),
                             (REQUESTED, FINAL, "N"))

    def test_redirect_needs_three_consistent_observations(self):
        for mutate in (lambda r: r["redirect_observations"].pop(),
                       lambda r: r["redirect_observations"].__setitem__(0, {"requested_url": REQUESTED, "final_url": REQUESTED})):
            result = redirect_result()
            mutate(result)
            with tempfile.TemporaryDirectory() as temp:
                self.shard(Path(temp), result)
                with self.assertRaises(ValueError):
                    candidates.load_collection(temp, "7")

    def test_failed_result_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            self.shard(Path(temp), failed())
            with self.assertRaises(ValueError):
                candidates.load_collection(temp, "7")


class AssessmentTests(unittest.TestCase):
    def build(self, record):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            epa = root / "epa"
            epa.mkdir()
            raw = b"[]"
            (epa / "samsung-current-rows.json").write_bytes(raw)
            (epa / "capture-summary.json").write_text(json.dumps({
                "status": "PASS", "dataset_id": "rxdj-2c88", "capture_run_id": "9", "row_count": 0,
                "rows_sha256": hashlib.sha256(raw).hexdigest()}))
            (root / "candidates.json").write_text(json.dumps({
                "contract": "G3_TABLET_EPA_SOURCE_CANDIDATES_V1", "status": "SOURCE_CANDIDATES_READY",
                "source_validation": "PASS", "dataset_id": "rxdj-2c88", "epa_capture_run_id": "9",
                "epa_samsung_row_count": 0, "population_count": 1, "records": [record]}))
            code = assessment.build(root / "candidates.json", epa, root / "out")
            return code, json.loads((root / "out" / "assessment.json").read_text())

    def test_repeated_redirect_is_medium_wrong_model_with_unknown_pdp_evidence(self):
        failure = {"requested_url": REQUESTED, "final_url": FINAL, "plp_stock_flag_raw": "N",
                   "redirect_observations": []}
        code, result = self.build({"exact_sku": SKU, "pdp_identity_failure": failure,
            "energy_star_claim_sources_raw": {"exact_sku": SKU, "plp_energy_star_flag_raw": "Y"}})
        self.assertEqual((code, result["status"], result["readiness_gaps"]), (0, "PASS", []))
        self.assertEqual(result["counts"], {"PASS": 0, "HIGH": 0, "MEDIUM": 1, "LOW": 0})
        row = result["records"][0]
        self.assertEqual(row["findings"], [{"control": "PDP_IDENTITY", "severity": "MEDIUM",
                                            "issue_code": "PDP_LINK_WRONG_MODEL"}])
        self.assertEqual(row["pdp_identity_failure"], failure)
        self.assertEqual(row["epa_current_registration"], "NOT_EVALUATED")
        points = row["publication_points"]
        self.assertEqual((points["plp_logo"]["state"], points["pdp_logo"]["state"],
                          points["spec_certification"]["state"]), ("PRESENT", "UNKNOWN", "UNKNOWN"))

    def test_redirect_without_urls_is_an_error_not_a_pass(self):
        with self.assertRaises(ValueError):
            self.build({"exact_sku": SKU, "pdp_identity_failure": {"requested_url": REQUESTED},
                "energy_star_claim_sources_raw": {"exact_sku": SKU}})

    def test_non_redirect_record_without_model_identity_still_blocks(self):
        code, result = self.build({"exact_sku": SKU,
            "energy_star_claim_sources_raw": {"exact_sku": SKU, "plp_energy_star_flag_raw": "Y"}})
        self.assertEqual((code, result["status"]), (1, "BLOCKED"))


if __name__ == "__main__":
    unittest.main()

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
import refresh_pages_tablet

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
IN_STOCK = {**PRODUCT, "source_claim_listing_raw": {**LISTING, "stockFlag": "Y"}}


class RetryTests(unittest.TestCase):
    def run_retry(self, first, later, in_stock=True):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pdp" / SKU).mkdir(parents=True)
            with patch.object(collect, "collect", side_effect=[[row] for row in later]):
                rows = collect.retry_failed([IN_STOCK if in_stock else PRODUCT], [first], root)
            return rows[0], json.loads((root / "pdp" / SKU / "result.json").read_text()) \
                if (root / "pdp" / SKU / "result.json").exists() else None

    def test_three_settled_identical_wrong_model_attempts_are_a_redirect_finding(self):
        row, written = self.run_retry(failed(), [failed(), failed()])
        self.assertEqual(row["status"], "PDP_REDIRECT_CONFIRMED")
        self.assertEqual(len(row["redirect_observations"]), 3)
        self.assertEqual(row["redirect_destination_sku"], "sm-x820nzaexar")
        self.assertEqual(row["source_claim_listing_raw"], IN_STOCK["source_claim_listing_raw"])
        self.assertEqual(written["status"], "PDP_REDIRECT_CONFIRMED")

    def test_controls_hydrating_during_loading_do_not_unsettle_a_stable_destination(self):
        grown = [{"url": FINAL, "selection": {**selection(), "selected_controls": controls}}
                 for controls in ([], [{"label": "Galaxy Tab S10+", "sku": "sm-x820nzaexar"}],
                                  [{"label": "Galaxy Tab S10+", "sku": "sm-x820nzaexar"},
                                   {"label": "512GB", "sku": "sm-x820nzaexar"}],
                                  [{"label": "Galaxy Tab S10+", "sku": "sm-x820nzaexar"},
                                   {"label": "512GB", "sku": "sm-x820nzaexar"}])]
        row = {**failed(), "identity_observations": grown}
        confirmed, _ = self.run_retry(row, [dict(row), dict(row)])
        self.assertEqual(confirmed["status"], "PDP_REDIRECT_CONFIRMED")

    def test_identity_moving_or_contradicted_by_controls_is_not_confirmed(self):
        moving = failed()
        moving["identity_observations"] = [moving["identity_observations"][0]] * 3 + [
            {"url": FINAL, "selection": selection("sm-x999nzaaxar")}]
        contradicted = failed()
        contradicted["identity_observations"] = [{"url": FINAL, "selection": {**selection(),
            "selected_controls": [{"label": "512GB", "sku": SKU.lower()}]}}] * 4
        for name, bad, reason in (("moving", moving, "SAMPLES_UNSETTLED"),
                                  ("contradicted", contradicted, "SELECTED_CONTROL_IS_REQUESTED_SKU")):
            with self.subTest(name):
                row, _ = self.run_retry(bad, [dict(bad), dict(bad)])
                self.assertEqual(row["status"], "FAILED")
                self.assertEqual({d["not_confirmed_because"] for d in row["attempt_diagnostics"]}, {reason})

    def test_out_of_stock_sku_landing_on_a_hub_is_confirmed_without_a_continue_control(self):
        hub = "https://www.samsung.com/us/tablets/galaxy-tab-s10/"
        timeout = {"exact_sku": SKU, "status": "FAILED", "requested_url": REQUESTED, "final_url": hub,
                   "http_status": 200, "failure_class": "SOURCE_COLLECTION_FAILED",
                   "error": "Locator.wait_for: Timeout 30000ms exceeded."}
        stocked = lambda flag: {**PRODUCT, "source_claim_listing_raw": {**LISTING, "stockFlag": flag}}
        for flag, status in (("N", "PDP_REDIRECT_CONFIRMED"), ("Y", "FAILED")):
            with self.subTest(stock=flag), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "pdp" / SKU).mkdir(parents=True)
                with patch.object(collect, "collect", side_effect=[[dict(timeout)], [dict(timeout)]]):
                    rows = collect.retry_failed([stocked(flag)], [dict(timeout)], root)
                self.assertEqual(rows[0]["status"], status)
                if status == "PDP_REDIRECT_CONFIRMED":
                    self.assertEqual(rows[0]["route_loss_kind"], "NON_PDP_PAGE")
                    self.assertEqual(len(rows[0]["redirect_observations"]), 3)

    def test_out_of_stock_hub_fallback_is_vetoed_by_a_control_naming_the_requested_sku(self):
        hub = "https://www.samsung.com/us/tablets/galaxy-tab-s10/"
        named = {"exact_sku": SKU, "status": "FAILED", "requested_url": REQUESTED, "final_url": hub,
                 "http_status": 200, "failure_class": "SOURCE_COLLECTION_FAILED", "error": "Timeout",
                 "selection_observed_raw": {"selected_controls": [{"label": "5G", "sku": SKU.lower()}]}}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pdp" / SKU).mkdir(parents=True)
            with patch.object(collect, "collect", side_effect=[[dict(named)], [dict(named)]]):
                rows = collect.retry_failed([PRODUCT], [dict(named)], root)
            self.assertEqual(rows[0]["status"], "FAILED")

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
        reasons = {"different destination": "DESTINATIONS_DIFFER_ACROSS_ATTEMPTS",
                   "http error": "HTTP_STATUS_OR_FALLBACK:503",
                   "unsettled samples": "SAMPLES_MISSING:3",
                   "other failure class": "FAILURE_CLASS:SOURCE_COLLECTION_FAILED",
                   "destination is the requested sku": "CONTINUE_SKU_IS_REQUESTED_SKU",
                   "continue sku not the url sku": "DESTINATION_URL_SKU_DIFFERS_FROM_CONTINUE_SKU"}
        for name, later in cases.items():
            with self.subTest(name):
                row, _ = self.run_retry(failed(), later)
                self.assertEqual(row["status"], "FAILED")
                found = {item["not_confirmed_because"] for item in row["attempt_diagnostics"]}
                self.assertIn(reasons[name], found)
                self.assertEqual(len(row["attempt_diagnostics"]), 3)

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
            self.assertEqual(claims[SKU], {"exact_sku": SKU, "plp_energy_star_flag_raw": "Y",
                                           "listing_title_raw": None})
            report = candidates.build_candidates(skus, products, records, claims, facts, [], "5",
                {"capture_run_id": "9"}, Path(temp) / "out")
            failure = report["records"][0]["pdp_identity_failure"]
            self.assertEqual((failure["requested_url"], failure["final_url"], failure["plp_stock_flag_raw"]),
                             (REQUESTED, FINAL, "N"))
            self.assertEqual(failure["destination"]["kind"], "UNLISTED_PDP")

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


class PagesCollectionTests(unittest.TestCase):
    def test_retry_and_archived_attempts_are_not_counted_as_results(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "shard-2"
            for where, status in (("pdp", "PDP_REDIRECT_CONFIRMED"), ("retry-1/pdp", "FAILED"),
                                  ("retry-2/pdp", "FAILED"), ("initial-attempt/pdp", "FAILED")):
                folder = root / where / SKU
                folder.mkdir(parents=True)
                (folder / "result.json").write_text(json.dumps({"exact_sku": SKU, "status": status}))
            other = Path(temp) / "shard-0" / "pdp" / "SM-X110NZAAXAR"
            other.mkdir(parents=True)
            (other / "result.json").write_text(json.dumps({"exact_sku": "SM-X110NZAAXAR", "status": "VERIFIED_EXACT_IDENTITY"}))
            rows = refresh_pages_tablet.collected_results(temp)
            self.assertEqual(sorted((row["exact_sku"], row["status"]) for row in rows),
                             [("SM-X110NZAAXAR", "VERIFIED_EXACT_IDENTITY"), (SKU, "PDP_REDIRECT_CONFIRMED")])


class AssessmentTests(unittest.TestCase):
    def build(self, record, epa_rows=()):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            epa = root / "epa"
            epa.mkdir()
            raw = json.dumps(list(epa_rows)).encode()
            (epa / "samsung-current-rows.json").write_bytes(raw)
            (epa / "capture-summary.json").write_text(json.dumps({
                "status": "PASS", "dataset_id": "rxdj-2c88", "capture_run_id": "9", "row_count": len(epa_rows),
                "rows_sha256": hashlib.sha256(raw).hexdigest()}))
            (root / "candidates.json").write_text(json.dumps({
                "contract": "G3_TABLET_EPA_SOURCE_CANDIDATES_V1", "status": "SOURCE_CANDIDATES_READY",
                "source_validation": "PASS", "dataset_id": "rxdj-2c88", "epa_capture_run_id": "9",
                "epa_samsung_row_count": len(epa_rows), "population_count": 1, "records": [record]}))
            code = assessment.build(root / "candidates.json", epa, root / "out")
            return code, json.loads((root / "out" / "assessment.json").read_text())

    def redirected(self, stock, destination=None, plp_flag="Y"):
        destination = destination or {"kind": "POPULATION_MEMBER", "sku": "SM-X820NZAEXAR", "final_url": FINAL}
        failure = {"requested_url": REQUESTED, "final_url": FINAL, "plp_stock_flag_raw": stock,
                   "redirect_observations": [], "destination": destination}
        claim = {"exact_sku": SKU, "plp_energy_star_flag_raw": plp_flag, "listing_title_raw": "SM-X828U"}
        return failure, {"exact_sku": SKU, "pdp_identity_failure": failure, "energy_star_claim_sources_raw": claim}

    def test_in_stock_redirect_is_medium_wrong_model_with_unknown_pdp_evidence(self):
        for stock in ("Y", None):
            with self.subTest(stock=stock):
                failure, record = self.redirected(stock)
                code, result = self.build(record)
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

    def test_out_of_stock_redirect_into_the_population_passes_with_the_redirect_noted(self):
        failure, record = self.redirected("N", plp_flag="Y")
        code, result = self.build(record)
        self.assertEqual((code, result["status"], result["readiness_gaps"]), (0, "PASS", []))
        self.assertEqual(result["counts"], {"PASS": 1, "HIGH": 0, "MEDIUM": 0, "LOW": 0})
        row = result["records"][0]
        self.assertEqual((row["grade"], row["findings"]), ("PASS", []))
        self.assertEqual(row["pdp_identity_failure"], failure)
        self.assertIn("SM-X820NZAEXAR", row["pdp_route_observation"]["note"])
        self.assertEqual(row["pdp_route_observation"]["finding"], "NONE")
        self.assertEqual(row["epa_current_registration"], "NOT_EVALUATED")
        points = row["publication_points"]
        self.assertEqual((points["plp_logo"]["state"], points["pdp_logo"]["state"],
                          points["spec_certification"]["state"]), ("PRESENT", "NOT_APPLICABLE", "NOT_APPLICABLE"))

    def test_out_of_stock_redirect_to_a_non_product_page_passes(self):
        _, record = self.redirected("N", {"kind": "NON_PDP_PAGE", "final_url": "https://www.samsung.com/us/tablets/"})
        code, result = self.build(record)
        self.assertEqual((code, result["records"][0]["grade"], result["records"][0]["findings"]), (0, "PASS", []))

    def test_out_of_stock_redirect_to_a_pdp_not_on_the_plp_is_low(self):
        _, record = self.redirected("N", {"kind": "UNLISTED_PDP", "sku_slug": "sm-x999", "final_url": FINAL})
        code, result = self.build(record)
        self.assertEqual((code, result["status"], result["counts"]), (0, "PASS", {"PASS": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 1}))
        row = result["records"][0]
        self.assertEqual(row["findings"], [{"control": "PDP_ROUTE", "severity": "LOW",
                                            "issue_code": "PDP_REDIRECT_TO_UNLISTED_PDP"}])
        self.assertEqual(row["pdp_route_observation"]["finding"], "PDP_REDIRECT_TO_UNLISTED_PDP")

    def test_out_of_stock_redirect_with_an_unclassified_destination_is_an_error(self):
        _, record = self.redirected("N")
        del record["pdp_identity_failure"]["destination"]
        with self.assertRaises(ValueError):
            self.build(record)

    def test_redirect_without_urls_is_an_error_not_a_pass(self):
        for stock in ("N", "Y"):
            with self.subTest(stock=stock), self.assertRaises(ValueError):
                self.build({"exact_sku": SKU, "pdp_identity_failure": {"requested_url": REQUESTED, "plp_stock_flag_raw": stock},
                    "energy_star_claim_sources_raw": {"exact_sku": SKU}})

    def test_non_redirect_record_without_model_identity_still_blocks(self):
        code, result = self.build({"exact_sku": SKU,
            "energy_star_claim_sources_raw": {"exact_sku": SKU, "plp_energy_star_flag_raw": "Y"}})
        self.assertEqual((code, result["status"]), (1, "BLOCKED"))


if __name__ == "__main__":
    unittest.main()

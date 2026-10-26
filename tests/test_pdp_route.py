import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exact_sku_retry
import pdp_route

SKU = "NS63CB755DSGAA"
REQUESTED = "https://www.samsung.com/us/home-appliance/x/y-sku-ns63cb755dsgaa/"
HUB = "https://www.samsung.com/us/home-appliances/family-hub/"
OTHER = "https://www.samsung.com/us/home-appliance/x/z-sku-ns63cb755dsgbb/"


def attempt(final=HUB, status="FAILED", http=200, requested=REQUESTED, error="Exact SKU is absent from rendered PDP text"):
    return {"exact_sku": SKU, "status": status, "requested_url": requested, "final_url": final,
            "http_status": http, "error": error}


def product(stock="N", flag="N"):
    return {"exact_sku": SKU, "source_claim_listing_raw": {"stockFlag": stock, "energyStarFlg": flag, "modelCode": SKU}}


class RouteLossTests(unittest.TestCase):
    def test_hub_and_other_model_destinations_are_route_loss(self):
        self.assertEqual(pdp_route.route_loss(attempt(HUB), SKU), (("NON_PDP_PAGE", HUB), None))
        self.assertEqual(pdp_route.route_loss(attempt(OTHER), SKU), (("OTHER_MODEL_PDP", OTHER), None))

    def test_other_failures_are_not_route_loss(self):
        cases = {
            "requested page itself": attempt(REQUESTED),
            "requested page without trailing slash": attempt(REQUESTED.rstrip("/")),
            "http error": attempt(http=503),
            "not failed": attempt(status="VERIFIED_EXACT_IDENTITY"),
            "other host": attempt("https://example.com/us/hub/"),
            "not https": attempt("http://www.samsung.com/us/hub/"),
            "outside the US store": attempt("https://www.samsung.com/uk/hub/"),
            "error page": attempt("https://www.samsung.com/us/error/"),
            "no final url": attempt(None),
        }
        for name, row in cases.items():
            with self.subTest(name):
                self.assertIsNone(pdp_route.route_loss(row, SKU)[0])

    def test_confirmation_needs_three_matching_attempts_and_stock_flag_n(self):
        three = [attempt(), attempt(), attempt()]
        terminal = pdp_route.confirm_route_loss(three, product("N"))
        self.assertEqual((terminal["status"], terminal["route_loss_kind"], len(terminal["redirect_observations"])),
                         ("PDP_REDIRECT_CONFIRMED", "NON_PDP_PAGE", 3))
        for name, attempts, item in (("in stock", three, product("Y")), ("stock unknown", three, product(None)),
                                     ("two attempts", three[:2], product("N")),
                                     ("different destinations", [attempt(), attempt(OTHER), attempt()], product("N")),
                                     ("one attempt reached the sku page", [attempt(), attempt(REQUESTED), attempt()], product("N"))):
            with self.subTest(name):
                self.assertIsNone(pdp_route.confirm_route_loss(attempts, item))

    def test_destination_is_classified_against_the_audited_population(self):
        other_sku = "NS63CB755DSGBB"
        classify = pdp_route.classify_destination
        self.assertEqual(classify(OTHER, [SKU, other_sku]), {"kind": "POPULATION_MEMBER", "sku": other_sku, "final_url": OTHER})
        self.assertEqual(classify(OTHER, [SKU])["kind"], "UNLISTED_PDP")
        self.assertEqual(classify(HUB, [SKU, other_sku])["kind"], "NON_PDP_PAGE")
        slashed = "https://www.samsung.com/us/x/y-sku-np740vjg-ka1us/"
        self.assertEqual(classify(slashed, ["NP740VJG-KA1US"])["sku"], "NP740VJG-KA1US")

    def test_outcome_follows_where_the_redirect_landed(self):
        for kind, expected in (("POPULATION_MEMBER", ("PASS", [])), ("NON_PDP_PAGE", ("PASS", [])),
                               ("UNLISTED_PDP", ("LOW", [{"control": "PDP_ROUTE", "severity": "LOW",
                                                          "issue_code": "PDP_REDIRECT_TO_UNLISTED_PDP"}]))):
            with self.subTest(kind):
                outcome, findings, observation = pdp_route.route_loss_outcome(
                    {"destination": {"kind": kind, "sku": "AB-1", "final_url": "u"}})
                self.assertEqual((outcome, findings), expected)
                self.assertEqual(observation["finding"], findings[0]["issue_code"] if findings else "NONE")
        with self.assertRaises(ValueError):
            pdp_route.route_loss_outcome({"destination": {"kind": "SOMETHING_ELSE"}})
        with self.assertRaises(ValueError):
            pdp_route.route_loss_outcome({})

    def test_points_keep_the_plp_flag_as_observed_and_mark_pdp_not_applicable(self):
        points = pdp_route.route_loss_points({"plp_energy_star_flag_raw": "Y"})
        self.assertEqual((points["plp_logo"]["state"], points["pdp_logo"]["state"], points["spec_certification"]["state"]),
                         ("PRESENT", "NOT_APPLICABLE", "NOT_APPLICABLE"))
        self.assertEqual(pdp_route.route_loss_points({"plp_energy_star_flag_raw": None})["plp_logo"]["state"], "UNKNOWN")

    def test_redirect_claim_carries_plp_facts_and_rejects_in_stock_results(self):
        terminal = pdp_route.confirm_route_loss([attempt(), attempt(), attempt()], product("N", "Y"))
        claim = pdp_route.redirect_claim(terminal, SKU, [SKU])
        self.assertEqual((claim["exact_sku"], claim["plp_energy_star_flag_raw"]), (SKU, "Y"))
        self.assertEqual(claim["pdp_route_loss_raw"]["plp_stock_flag_raw"], "N")
        self.assertEqual(claim["pdp_route_loss_raw"]["destination"]["kind"], "NON_PDP_PAGE")
        self.assertNotIn("pdp_facts_raw", claim)
        in_stock = {**terminal, "source_claim_listing_raw": {"stockFlag": "Y"}}
        with self.assertRaises(ValueError):
            pdp_route.redirect_claim(in_stock, SKU, [SKU])
        with self.assertRaises(ValueError):
            pdp_route.redirect_claim({**terminal, "redirect_observations": terminal["redirect_observations"][:2]}, SKU, [SKU])


class SharedRetryTests(unittest.TestCase):
    def run_retry(self, item, later, confirm=True):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pdp" / SKU).mkdir(parents=True)
            (root / "pdp" / SKU / "result.json").write_text('{"first": true}')
            outcomes = iter(later)

            def collector(products, destination):
                return [next(outcomes)]

            rows = exact_sku_retry.retry_failed([item], root, [attempt()], collector, sleep=lambda _: None,
                                                confirm_route_loss=confirm)
            written = json.loads((root / "pdp" / SKU / "result.json").read_text())
            archived = (root / "retries" / "previous-attempts" / SKU / "attempt-1" / "result.json")
            return rows[0], written, archived.exists() and json.loads(archived.read_text())

    def test_out_of_stock_route_loss_is_confirmed_and_the_first_attempt_is_archived(self):
        row, written, archived = self.run_retry(product("N"), [attempt(), attempt()])
        self.assertEqual(row["status"], "PDP_REDIRECT_CONFIRMED")
        self.assertEqual(written["status"], "PDP_REDIRECT_CONFIRMED")
        self.assertEqual(archived, {"first": True})

    def test_in_stock_or_disabled_route_loss_stays_a_failure_with_readable_reasons(self):
        row, written, archived = self.run_retry(product("Y"), [attempt(), attempt()])
        self.assertEqual(row["status"], "FAILED")
        self.assertEqual({d["not_confirmed_because"] for d in row["route_loss_diagnostics"]}, {"STOCK_FLAG_NOT_N"})
        self.assertEqual((written, archived), ({"first": True}, False))
        disabled, _, _ = self.run_retry(product("N"), [attempt(), attempt()], confirm=False)
        self.assertEqual(disabled["status"], "FAILED")
        self.assertNotIn("route_loss_diagnostics", disabled)

    def test_a_verified_retry_is_not_a_route_loss(self):
        verified = {"exact_sku": SKU, "status": "VERIFIED_EXACT_IDENTITY"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pdp" / SKU).mkdir(parents=True)
            retry_dir = root / "retries" / "attempt-2" / "pdp" / SKU
            retry_dir.mkdir(parents=True)

            def collector(products, destination):
                return [verified]

            rows = exact_sku_retry.retry_failed([product("N")], root, [attempt()], collector,
                                                sleep=lambda _: None, confirm_route_loss=True)
            self.assertEqual(rows[0]["status"], "VERIFIED_EXACT_IDENTITY")


FAMILY_MODULES = {
    "range": ("g3_range_epa_candidates", "g3_range_energy_star_assessment"),
    "cooktop": ("g3_cooktop_epa_candidates", "g3_cooktop_energy_star_assessment"),
    "hood": ("g3_hood_epa_candidates", "g3_hood_energy_star_assessment"),
    "monitor": ("g3_monitor_epa_candidates", "g3_monitor_energy_star_assessment"),
}


OTHER_SKU = "NS63CB755DSGBB"


def terminal_row(sku, final, stock="N", flag="N", other=None):
    requested = f"https://www.samsung.com/us/home-appliance/x/y-sku-{sku.lower()}/"
    item = {"exact_sku": sku, "source_claim_listing_raw": {"stockFlag": stock, "energyStarFlg": flag, "modelCode": sku}}
    row = attempt(final=final, requested=requested)
    row["exact_sku"] = sku
    return pdp_route.confirm_route_loss([row, dict(row), dict(row)], item) or {
        **row, "status": "PDP_REDIRECT_CONFIRMED", "redirect_observations": [row] * 3,
        "source_claim_listing_raw": item["source_claim_listing_raw"]}


class FamilyPipelineTests(unittest.TestCase):
    """Every EPA-only family settles a confirmed route loss by where the redirect landed."""

    def write_sources(self, root, candidates, rows):
        collection = root / "collection"
        (collection / "pdp").mkdir(parents=True)
        (collection / "collection-summary.json").write_text(json.dumps({
            "status": "PASS", "contract": candidates.COLLECTION_CONTRACT, "collection_run_id": "123",
            "coverage": {"population_count": len(rows)}}))
        (collection / "products.json").write_text(json.dumps([{"exact_sku": row["exact_sku"]} for row in rows]))
        for row in rows:
            (collection / "pdp" / row["exact_sku"]).mkdir()
            (collection / "pdp" / row["exact_sku"] / "result.json").write_text(json.dumps(row))
        epa = root / "epa"
        epa.mkdir()
        raw = b"[]"
        (epa / "samsung-current-rows.json").write_bytes(raw)
        (epa / "capture-summary.json").write_text(json.dumps({
            "status": "PASS", "contract": candidates.EPA_CONTRACT, "dataset_id": candidates.DATASET,
            "capture_run_id": "9", "row_count": 0, "rows_sha256": hashlib.sha256(raw).hexdigest()}))
        return collection, epa

    def assess_all(self, family, rows):
        candidates = importlib.import_module(FAMILY_MODULES[family][0])
        assessor = importlib.import_module(FAMILY_MODULES[family][1])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            collection, epa = self.write_sources(root, candidates, rows)
            candidates.build(collection, "123", epa, "9", root / "candidates")
            report = json.loads(next((root / "candidates").glob("*-source-candidates.json")).read_text())
            return {record["exact_sku"]: assessor.assess_record(record) for record in report["records"]}

    def test_redirect_into_the_population_passes_with_the_redirect_noted(self):
        member_url = f"https://www.samsung.com/us/home-appliance/x/z-sku-{OTHER_SKU.lower()}/"
        rows = [terminal_row(SKU, member_url), terminal_row(OTHER_SKU, HUB)]
        for family in FAMILY_MODULES:
            with self.subTest(family=family):
                result = self.assess_all(family, rows)[SKU]
                self.assertEqual((result["display_outcome"], result["findings"]), ("PASS", []))
                self.assertEqual(result["pdp_identity_failure"]["destination"], {"kind": "POPULATION_MEMBER", "sku": OTHER_SKU, "final_url": member_url})
                self.assertIn(OTHER_SKU, result["pdp_route_observation"]["note"])
                points = result["energy_star_publication"]["points"]
                self.assertEqual((points["pdp_logo"]["state"], points["spec_certification"]["state"]), ("NOT_APPLICABLE", "NOT_APPLICABLE"))
                self.assertEqual(result["epa_current_registration"]["state"], "NOT_EVALUATED")

    def test_redirect_to_a_non_product_page_passes_and_to_an_unlisted_pdp_is_low(self):
        unlisted = "https://www.samsung.com/us/home-appliance/x/q-sku-zz999unlisted/"
        rows = [terminal_row(SKU, HUB), terminal_row(OTHER_SKU, unlisted)]
        for family in FAMILY_MODULES:
            with self.subTest(family=family):
                results = self.assess_all(family, rows)
                self.assertEqual((results[SKU]["display_outcome"], results[SKU]["findings"]), ("PASS", []))
                low = results[OTHER_SKU]
                self.assertEqual(low["display_outcome"], "LOW")
                self.assertEqual([f["issue_code"] for f in low["findings"]], ["PDP_REDIRECT_TO_UNLISTED_PDP"])
                self.assertEqual(low["pdp_route_observation"]["finding"], "PDP_REDIRECT_TO_UNLISTED_PDP")

    def test_the_plp_flag_is_not_compared_with_epa_for_a_route_loss_sku(self):
        for family in FAMILY_MODULES:
            with self.subTest(family=family):
                result = self.assess_all(family, [terminal_row(SKU, HUB, flag="Y")])[SKU]
                self.assertEqual((result["display_outcome"], result["findings"]), ("PASS", []))
                self.assertEqual(result["energy_star_publication"]["points"]["plp_logo"]["state"], "PRESENT")

    def test_a_confirmed_result_for_an_in_stock_sku_is_rejected(self):
        bad = terminal_row(SKU, HUB)
        bad["source_claim_listing_raw"] = {**bad["source_claim_listing_raw"], "stockFlag": "Y"}
        for family in FAMILY_MODULES:
            with self.subTest(family=family), self.assertRaises(ValueError):
                self.assess_all(family, [bad])

    def test_dryer_collection_accepts_the_confirmed_result_and_settles_it_by_destination(self):
        candidates = importlib.import_module("g3_dryer_epa_claim_candidates")
        assessor = importlib.import_module("g3_dryer_energy_star_assessment")
        unlisted = "https://www.samsung.com/us/home-appliance/x/q-sku-zz999unlisted/"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            collection = root / "collection"
            (collection / "pdp").mkdir(parents=True)
            rows = [terminal_row(SKU, HUB), terminal_row(OTHER_SKU, unlisted)]
            (collection / "collection-summary.json").write_text(json.dumps({
                "status": "PASS", "contract": "G3_DRYER_EXACT_SKU_PDP_V1", "collection_run_id": "123",
                "coverage": {"population_count": 2}}))
            (collection / "products.json").write_text(json.dumps([{"exact_sku": row["exact_sku"]} for row in rows]))
            for row in rows:
                (collection / "pdp" / row["exact_sku"]).mkdir()
                (collection / "pdp" / row["exact_sku"] / "result.json").write_text(json.dumps(row))
            claims, _ = candidates.load_collection(collection, "123")
            (root / "rows.json").write_text(json.dumps({
                "contract": "G3_DRYER_EPA_CLAIM_CANDIDATES_V1", "status": "SOURCE_CANDIDATES_READY",
                "source_validation": "PASS", "population_count": 2,
                "rows": [{"exact_sku": row["exact_sku"], "energy_star_claim_sources_raw": claims[row["exact_sku"]],
                          "dryer_epa_model_pattern_candidates": [], "combo_epa_model_pattern_candidates": []} for row in rows]}))
            assessor.build(root / "rows.json", root / "out")
            records = {r["exact_sku"]: r for r in json.loads(next((root / "out").glob("*.json")).read_text())["records"]}
            self.assertEqual((records[SKU]["display_outcome"], records[SKU]["findings"]), ("PASS", []))
            self.assertEqual(records[OTHER_SKU]["display_outcome"], "LOW")
            self.assertEqual(records[SKU]["energy_star_publication"]["points"]["pdp_logo"]["state"], "NOT_APPLICABLE")


if __name__ == "__main__":
    unittest.main()

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

    def test_redirect_claim_carries_plp_facts_and_rejects_in_stock_results(self):
        terminal = pdp_route.confirm_route_loss([attempt(), attempt(), attempt()], product("N", "Y"))
        claim = pdp_route.redirect_claim(terminal, SKU)
        self.assertEqual((claim["exact_sku"], claim["plp_energy_star_flag_raw"]), (SKU, "Y"))
        self.assertEqual(claim["pdp_route_loss_raw"]["plp_stock_flag_raw"], "N")
        self.assertNotIn("pdp_facts_raw", claim)
        in_stock = {**terminal, "source_claim_listing_raw": {"stockFlag": "Y"}}
        with self.assertRaises(ValueError):
            pdp_route.redirect_claim(in_stock, SKU)
        with self.assertRaises(ValueError):
            pdp_route.redirect_claim({**terminal, "redirect_observations": terminal["redirect_observations"][:2]}, SKU)


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


class FamilyPipelineTests(unittest.TestCase):
    def write_sources(self, root, candidates, plp_flag, stock="N"):
        collection = root / "collection"
        (collection / "pdp" / SKU).mkdir(parents=True)
        (collection / "collection-summary.json").write_text(json.dumps({
            "status": "PASS", "contract": candidates.COLLECTION_CONTRACT, "collection_run_id": "123",
            "coverage": {"population_count": 1}}))
        (collection / "products.json").write_text(json.dumps([{"exact_sku": SKU}]))
        terminal = pdp_route.confirm_route_loss([attempt(), attempt(), attempt()], product(stock, plp_flag)) \
            or {**attempt(), "status": "PDP_REDIRECT_CONFIRMED", "redirect_observations": [attempt()] * 3,
                "source_claim_listing_raw": product(stock, plp_flag)["source_claim_listing_raw"]}
        (collection / "pdp" / SKU / "result.json").write_text(json.dumps(terminal))
        epa = root / "epa"
        epa.mkdir()
        raw = b"[]"
        (epa / "samsung-current-rows.json").write_bytes(raw)
        (epa / "capture-summary.json").write_text(json.dumps({
            "status": "PASS", "contract": candidates.EPA_CONTRACT, "dataset_id": candidates.DATASET,
            "capture_run_id": "9", "row_count": 0, "rows_sha256": hashlib.sha256(raw).hexdigest()}))
        return collection, epa

    def assess(self, family, plp_flag, stock="N"):
        candidates = importlib.import_module(FAMILY_MODULES[family][0])
        assessor = importlib.import_module(FAMILY_MODULES[family][1])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            collection, epa = self.write_sources(root, candidates, plp_flag, stock)
            candidates.build(collection, "123", epa, "9", root / "candidates")
            report = json.loads(next((root / "candidates").glob("*-source-candidates.json")).read_text())
            return assessor.assess_record(report["records"][0])

    def test_out_of_stock_route_loss_is_evidence_only_and_the_plp_point_is_assessed(self):
        for family in FAMILY_MODULES:
            with self.subTest(family=family):
                passing = self.assess(family, "N")
                self.assertEqual((passing["display_outcome"], passing["findings"]), ("PASS", []))
                self.assertEqual(passing["pdp_route_observation"]["finding"], "NONE")
                self.assertEqual(passing["pdp_identity_failure"]["plp_stock_flag_raw"], "N")
                points = passing["energy_star_publication"]["points"]
                self.assertEqual((points["plp_logo"]["state"], points["pdp_logo"]["state"],
                                  points["spec_certification"]["state"]), ("ABSENT", "NOT_APPLICABLE", "NOT_APPLICABLE"))
                # PLP point present while no current EPA registration exists is still a HIGH finding
                self.assertEqual(self.assess(family, "Y")["display_outcome"], "HIGH")

    def test_a_confirmed_result_for_an_in_stock_sku_is_rejected(self):
        for family in FAMILY_MODULES:
            with self.subTest(family=family), self.assertRaises(ValueError):
                self.assess(family, "N", stock="Y")

    def test_dryer_collection_accepts_the_confirmed_result_and_assesses_the_plp_point(self):
        candidates = importlib.import_module("g3_dryer_epa_claim_candidates")
        assessor = importlib.import_module("g3_dryer_energy_star_assessment")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            collection = root / "collection"
            (collection / "pdp" / SKU).mkdir(parents=True)
            (collection / "collection-summary.json").write_text(json.dumps({
                "status": "PASS", "contract": "G3_DRYER_EXACT_SKU_PDP_V1", "collection_run_id": "123",
                "coverage": {"population_count": 1}}))
            (collection / "products.json").write_text(json.dumps([{"exact_sku": SKU}]))
            terminal = pdp_route.confirm_route_loss([attempt(), attempt(), attempt()], product("N", "N"))
            (collection / "pdp" / SKU / "result.json").write_text(json.dumps(terminal))
            claims, _ = candidates.load_collection(collection, "123")
            (root / "rows.json").write_text(json.dumps({
                "contract": "G3_DRYER_EPA_CLAIM_CANDIDATES_V1", "status": "SOURCE_CANDIDATES_READY",
                "source_validation": "PASS", "population_count": 1,
                "rows": [{"exact_sku": SKU, "energy_star_claim_sources_raw": claims[SKU],
                          "dryer_epa_model_pattern_candidates": [], "combo_epa_model_pattern_candidates": []}]}))
            assessor.build(root / "rows.json", root / "out")
            result = json.loads(next((root / "out").glob("*.json")).read_text())
            record = result["records"][0]
            self.assertEqual((record["display_outcome"], record["findings"]), ("PASS", []))
            self.assertEqual(record["pdp_identity_failure"]["plp_stock_flag_raw"], "N")
            self.assertEqual(record["energy_star_publication"]["points"]["pdp_logo"]["state"], "NOT_APPLICABLE")


if __name__ == "__main__":
    unittest.main()

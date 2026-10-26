import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import plp_population
import source_recon
from source_contract import SpecsSupportIdentityError, pdp_facts

BUNDLE = {"modelCode": "F-1212121212461", "group_id": "g0", "modelName": "Bundle", "pdpURL": "/us/x/", "ecomFlag": "Y"}
MONITOR = {"modelCode": "LS27FM503ENXZA", "group_id": "g1", "modelName": "Monitor", "pdpURL": "/us/y/", "ecomFlag": "Y"}


class FirstIdentifiableSampleTests(unittest.TestCase):
    def run_selection(self, candidates, outcomes, limit=6):
        calls, kept = [], []

        def run_pdp(product):
            calls.append(product)
            outcome = outcomes[len(calls) - 1]
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        result = source_recon.first_identifiable_sample(
            candidates, run_pdp, lambda product: {"rendered_card": True},
            lambda index, product: kept.append((index, product["modelCode"])) or f"skipped-samples/{index}", limit)
        return result, calls, kept

    def test_first_candidate_is_used_when_it_is_identifiable(self):
        result, calls, kept = self.run_selection([MONITOR, BUNDLE], [{"target_sku": "A"}])
        self.assertEqual((result, calls, kept), ({"target_sku": "A", "skipped_samples": []}, [MONITOR], []))

    def test_identity_shape_failure_advances_and_is_reported_with_preserved_evidence(self):
        result, calls, kept = self.run_selection([BUNDLE, MONITOR], [SpecsSupportIdentityError("specs=0, support=1"), {"target_sku": "B"}])
        self.assertEqual(calls, [BUNDLE, MONITOR])
        self.assertEqual(kept, [(0, "F-1212121212461")])
        skipped = result["skipped_samples"][0]
        self.assertEqual((skipped["sku"], skipped["error"], skipped["plp_exposure"], skipped["preserved"]),
                         ("F-1212121212461", "specs=0, support=1", {"rendered_card": True}, "skipped-samples/0"))

    def test_other_failures_are_not_skipped(self):
        with self.assertRaises(AssertionError):
            self.run_selection([BUNDLE, MONITOR], [AssertionError("PDP HTTP access failed"), {"target_sku": "B"}])

    def test_exhausting_the_bound_is_a_failure_that_names_every_skipped_sample(self):
        errors = [SpecsSupportIdentityError("e1"), SpecsSupportIdentityError("e2")]
        with self.assertRaises(ValueError) as caught:
            self.run_selection([BUNDLE, MONITOR, MONITOR], errors + [{"target_sku": "C"}], limit=2)
        self.assertIn("F-1212121212461", str(caught.exception))
        self.assertIn("e2", str(caught.exception))


def entry(sku, url, group="g"):
    return {"exact_sku": sku, "source_claim_listing_raw": {"modelCode": sku, "energyStarFlg": "Y"},
            "listings": [{"source_family_id": group, "pdp_url": url}]}


BUNDLE_URL = "https://www.samsung.com/us/monitors/gaming/27-inch-monitor-bundle-sku-f-1212121212458/"


class BundleExclusionTests(unittest.TestCase):
    def test_predicate_requires_both_the_code_shape_and_the_bundle_url(self):
        is_bundle = plp_population.is_monitor_bundle_entry
        self.assertTrue(is_bundle("F-1212121212458", BUNDLE_URL))
        self.assertTrue(is_bundle("F-1212121212458", BUNDLE_URL.rstrip("/").upper()))
        self.assertFalse(is_bundle("F-1212121212458", "https://www.samsung.com/us/monitors/x-sku-f-1212121212458/"))
        self.assertFalse(is_bundle("LS27FM503ENXZA", "https://www.samsung.com/us/monitors/x-bundle-sku-ls27fm503enxza/"))
        self.assertFalse(is_bundle("F-12AB", "https://www.samsung.com/us/monitors/x-bundle-sku-f-12ab/"))
        self.assertFalse(is_bundle("F-1212121212458", None))

    def test_bundles_leave_population_but_keep_card_and_listing_evidence(self):
        products = [entry("F-1212121212458", BUNDLE_URL, "g0"),
                    entry("LS27FM503ENXZA", "https://www.samsung.com/us/monitors/x-sku-ls27fm503enxza/", "g1")]
        cards = {"F-1212121212458": {"sku": "F-1212121212458"}, "LS27FM503ENXZA": {"sku": "LS27FM503ENXZA"}}
        kept, kept_cards, expected, excluded = plp_population.split_monitor_bundles(products, cards, 2)
        self.assertEqual([p["exact_sku"] for p in kept], ["LS27FM503ENXZA"])
        self.assertEqual((set(kept_cards), expected), ({"LS27FM503ENXZA"}, 1))
        self.assertEqual(plp_population.select_listed_products(kept, kept_cards, expected), kept)
        row = excluded[0]
        self.assertEqual((row["exact_sku"], row["exclusion_basis"], row["source_family_id"], row["pdp_url"]),
                         ("F-1212121212458", plp_population.BUNDLE_EXCLUSION_BASIS, "g0", BUNDLE_URL))
        self.assertEqual(row["rendered_plp_card"], {"sku": "F-1212121212458"})
        self.assertEqual(row["source_claim_listing_raw"]["energyStarFlg"], "Y")

    def test_population_without_bundles_is_unchanged(self):
        products = [entry("LS27FM503ENXZA", "https://www.samsung.com/us/monitors/x-sku-ls27fm503enxza/")]
        cards = {"LS27FM503ENXZA": {}}
        kept, kept_cards, expected, excluded = plp_population.split_monitor_bundles(products, cards, 1)
        self.assertEqual((kept, kept_cards, expected, excluded), (products, cards, 1, []))


class ExposureAndErrorTests(unittest.TestCase):
    def test_plp_exposure_reports_card_group_and_element_presence(self):
        observation = {"rendered_tiles": [{"sku": "LS27FM503ENXZA"}], "rendered_tile_groups": ["g1"],
                       "rendered_candidates": [{"sku": "LS27FM503ENXZA"}, {"sku": "LS27FM503ENXZA"}]}
        self.assertEqual(source_recon.plp_exposure(observation, MONITOR),
                         {"rendered_card": True, "group_has_rendered_card": True, "rendered_modelcode_elements": 2})
        self.assertEqual(source_recon.plp_exposure(observation, BUNDLE),
                         {"rendered_card": False, "group_has_rendered_card": False, "rendered_modelcode_elements": 0})
        self.assertEqual(source_recon.plp_exposure({}, BUNDLE), "UNKNOWN")

    def test_missing_specs_record_raises_the_identity_error_with_diagnostics(self):
        data = {"Specs": [{"modelCode": "LS27FM503ENXZA", "fullSpecs": []}],
                "Support": [{"modelCode": "F-1212121212461", "supports": []}]}
        with self.assertRaises(SpecsSupportIdentityError) as caught:
            pdp_facts(data, "F-1212121212461", family="monitor")
        self.assertIn("specs=0, support=1", str(caught.exception))
        self.assertIsInstance(caught.exception, ValueError)


if __name__ == "__main__":
    unittest.main()

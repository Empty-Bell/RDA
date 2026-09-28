from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from g2_energyguide_model_pattern_assessment import build_assessment  # noqa: E402


class ModelPatternAssessmentTests(unittest.TestCase):
    def inputs(self):
        values = {
            "RF18A5101SR/AA": "RF18A5101",
            "RF90F23AECEAA": "RF90F23BE*; RF90F23AE*, RF90F23AE**",
            "RF27CG5400SRAA": "RF27CG5400*",
        }
        bundle = {
            "manifest": {"run_id": "run-1"},
            "products": [{"exact_sku": sku} for sku in values],
            "facts": [{"kind": "ENERGYGUIDE", "exact_sku": sku, "observations": {
                "label_model_raw": {"state": "VALUE", "value": raw},
                "document_sha256": {"state": "VALUE", "value": "a" * 64},
            }} for sku, raw in values.items()],
        }
        review = {"contract": "CAPACITY_MODEL_REVIEW_PROJECTION_ONLY", "records": []}
        return bundle, review

    def test_full_population_prefix_and_multiple_tokens(self):
        bundle, review = self.inputs()
        result = build_assessment(bundle, review)
        self.assertEqual(result["counts"]["display"], {"PASS": 3, "NOT_EVALUATED": 0})
        by_sku = {row["exact_sku"]: row for row in result["records"]}
        self.assertEqual(by_sku["RF18A5101SR/AA"]["matching_patterns"], ["RF18A5101"])
        self.assertEqual(by_sku["RF90F23AECEAA"]["matching_patterns"], ["RF90F23AE*", "RF90F23AE**"])
        self.assertEqual(by_sku["RF27CG5400SRAA"]["matching_patterns"], ["RF27CG5400*"])

    def test_nonmatching_tokens_remain_unresolved(self):
        bundle, review = self.inputs()
        bundle["facts"][0]["observations"]["label_model_raw"]["value"] = "RF19A5101"
        result = build_assessment(bundle, review)
        self.assertEqual(result["counts"]["display"], {"PASS": 2, "NOT_EVALUATED": 1})

    def test_extra_trailing_stars_may_be_empty(self):
        bundle,review=self.inputs()
        bundle["facts"][0]["observations"]["label_model_raw"]["value"]="RF18A5101SR*****"
        result=build_assessment(bundle,review)
        self.assertEqual(result["counts"]["display"],{"PASS":3,"NOT_EVALUATED":0})

    def test_missing_fact_or_changed_review_pdf_fails(self):
        bundle, review = self.inputs()
        bundle["facts"].pop()
        with self.assertRaisesRegex(ValueError, "cover"):
            build_assessment(bundle, review)
        bundle, review = self.inputs()
        review["records"] = [{"exact_skus": ["RF18A5101SR/AA"], "pdf_sha256": "b" * 64}]
        with self.assertRaisesRegex(ValueError, "hash differs"):
            build_assessment(bundle, review)

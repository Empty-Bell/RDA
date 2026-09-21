from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from g2_energyguide_model_pattern_assessment import build_assessment  # noqa: E402


class ModelPatternAssessmentTests(unittest.TestCase):
    def review(self):
        return {"contract": "CAPACITY_MODEL_REVIEW_PROJECTION_ONLY", "records": [{
            "pdf_sha256": "a" * 64,
            "exact_skus": ["RF90F23AEWAA", "RF90F23AECEAA", "RF90F23AECRAA"],
            "model_review": "SOURCE_LABEL_EXPLICITLY_LISTS_TWO_PATTERNS_IDENTITY_NOT_EVALUATED",
            "model_text_raw": "Models RF90F23AE*, RF90F23AE**",
            "model_tokens_raw": ["RF90F23AE*", "RF90F23AE**"],
        }]}

    def test_each_reviewed_sku_passes_when_one_pattern_matches(self):
        result = build_assessment({"manifest": {"run_id": "run-1"}}, self.review())
        self.assertEqual(result["counts"]["display"], {"PASS": 3, "NOT_EVALUATED": 0})
        by_sku = {row["exact_sku"]: row for row in result["records"]}
        self.assertEqual(by_sku["RF90F23AEWAA"]["matching_patterns"], ["RF90F23AE*"])
        self.assertEqual(by_sku["RF90F23AECEAA"]["matching_patterns"], ["RF90F23AE**"])
        self.assertEqual(by_sku["RF90F23AECRAA"]["assessment"], "MODEL_PATTERN_INCLUDED")

    def test_pattern_outside_reviewed_group_is_not_assessed(self):
        review = self.review()
        review["records"][0]["model_review"] = "RENDER_AND_RAW_DESCRIPTOR_AGREE_IDENTITY_NOT_EVALUATED"
        with self.assertRaisesRegex(ValueError, "scope"):
            build_assessment({"manifest": {"run_id": "run-1"}}, review)


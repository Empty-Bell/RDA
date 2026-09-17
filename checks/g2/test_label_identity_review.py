"""Preserve actual OCR model damage separately from visual review annotations."""

import json
from pathlib import Path
import unittest

from energyguide_fields import label_candidates

ROOT = Path(__file__).resolve().parents[2]


class LabelIdentityReviewTests(unittest.TestCase):
    def setUp(self):
        self.review = json.loads((ROOT / "docs/evidence/g2-capacity-model-review.json").read_text(encoding="utf-8"))

    def test_raw_descriptors_are_not_replaced_by_visual_transcriptions(self):
        for record in self.review["records"]:
            with self.subTest(pdf=record["pdf_sha256"]):
                text = "\n".join([record["model_text_raw"], record["capacity_text_raw"],
                                  "Both cost ranges based on models of similar size capacity."])
                parsed = label_candidates(text, self.review["engine"], record["pdf_sha256"])
                self.assertEqual(parsed["model_candidates_raw"][0]["value_raw"], record["model_token_raw"])
                self.assertEqual(parsed["model_candidates_raw"][0]["context_raw"], record["model_text_raw"])
                self.assertEqual(len(parsed["capacity_candidates_raw"]), 2)
                self.assertEqual(parsed["capacity_candidates_raw"][0]["value_raw"], record["capacity_text_raw"])
                self.assertEqual(parsed["wildcard_correction"], "NOT_APPLIED")
                self.assertEqual(parsed["identity_matching"], "NOT_EVALUATED")

    def test_token_without_star_does_not_resolve_visible_wildcard_damage(self):
        damaged = [record for record in self.review["records"] if record["model_review"].startswith("OCR_")]
        self.assertEqual(len(damaged), 2)
        for record in damaged:
            with self.subTest(pdf=record["pdf_sha256"]):
                parsed = label_candidates(record["model_text_raw"], self.review["engine"], record["pdf_sha256"])
                candidate = parsed["model_candidates_raw"][0]
                self.assertEqual(candidate["wildcard_count_status"], "NO_WILDCARD_OBSERVED")
                self.assertNotEqual(candidate["value_raw"], record["model_visual_transcription"])
                self.assertFalse(self.review["model_correction_enabled"])
                self.assertFalse(self.review["sku_identity_matching_enabled"])

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from energyguide_fields import annual_layout_candidates, label_candidates
from g2_label_activation import load_review_annotations, select_live_reviewed_energy


class LabelActivationTests(unittest.TestCase):
    def setUp(self):
        source = json.loads((ROOT / "tests/fixtures/energyguide-fields/refrigerator.json").read_text(encoding="utf-8"))
        spans = json.loads((ROOT / "tests/fixtures/energyguide-fields/refrigerator-layout.json").read_text(encoding="utf-8"))["spans"]
        self.result = {"sha256": source["sha256"]}
        self.candidates = label_candidates("\n".join(source["ocr_raw_texts"]), source["extraction_engine"], source["sha256"])
        self.layout = annual_layout_candidates(spans, source["sha256"])
        layout = self.layout["annual_layout_candidates"][0]
        proposal = layout["nearest_proposal_raw"]
        self.review = {"pdf_sha256": source["sha256"], "document_count": 1,
                       "all_pages_reviewed": True, "us_panel_verified": True, "page": 0,
                       "caption_detection": layout["caption_detection"],
                       "number_detection": proposal["number_detection"], "unit_detection": proposal["unit_detection"]}

    def test_live_bytes_must_match_review_before_selection(self):
        selected = select_live_reviewed_energy("SKU", self.result, self.candidates, self.layout, {"SKU": self.review})
        self.assertEqual(selected["observation"]["state"], "VALUE")
        changed = copy.deepcopy(self.result)
        changed["sha256"] = "0" * 64
        self.assertEqual(select_live_reviewed_energy("SKU", changed, self.candidates, self.layout, {"SKU": self.review})["observation"]["state"], "NOT_OBSERVED")

    def test_missing_review_annotation_never_selects(self):
        selected = select_live_reviewed_energy("SKU", self.result, self.candidates, self.layout, {})
        self.assertEqual(selected["observation"]["state"], "NOT_OBSERVED")

    def test_saved_annotations_have_one_mapping_per_replayed_sku(self):
        reviews = load_review_annotations(ROOT / "docs/evidence/g2-label-review-annotations.json")
        self.assertEqual(len(reviews), 9)
        self.assertIn("RF22A4111SR/AA", reviews)

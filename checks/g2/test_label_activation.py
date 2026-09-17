import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from energyguide_fields import annual_layout_candidates, label_candidates
from g2_label_activation import (load_capacity_review_annotations, load_review_annotations,
    select_live_reviewed_capacity, select_live_reviewed_energy, summarize_capacity_selection_outcomes,
    summarize_selection_outcomes)


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

    def test_summary_is_observation_only_and_rejects_duplicate_document(self):
        selection = select_live_reviewed_energy("SKU", self.result, self.candidates, self.layout, {"SKU": self.review})
        record = {"exact_sku": "SKU", "source_document_index": 0, "pdf_sha256": self.result["sha256"], "selection": selection}
        summary = summarize_selection_outcomes([record])
        self.assertEqual(summary["contract"], "REVIEW_BOUND_LIVE_OBSERVATION_ONLY")
        self.assertEqual(summary["counts"], {"VALUE": 1, "NOT_OBSERVED": 0})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            summarize_selection_outcomes([record, record])

    def test_capacity_review_requires_matching_live_bytes(self):
        reviews = load_capacity_review_annotations(ROOT / "docs/evidence/g2-capacity-model-review.json")
        review = dict(reviews["RF22A4221SR/AA"], pdf_sha256=self.result["sha256"],
                      capacity_text_raw="Capacity: 28.6 Cubic Feet")
        candidates = copy.deepcopy(self.candidates)
        candidates["capacity_candidates_raw"] = [{"value_raw": "Capacity: 28.6 Cubic Feet", "line": 0}]
        selected = select_live_reviewed_capacity("RF22A4221SR/AA", self.result, candidates,
                                                 {"RF22A4221SR/AA": review})
        self.assertEqual(selected["observation"]["state"], "VALUE")
        changed = dict(self.result, sha256="0" * 64)
        self.assertEqual(select_live_reviewed_capacity("RF22A4221SR/AA", changed, candidates,
                         {"RF22A4221SR/AA": review})["observation"]["state"], "NOT_OBSERVED")
        summary = summarize_capacity_selection_outcomes([{"exact_sku": "SKU", "source_document_index": 0,
            "pdf_sha256": self.result["sha256"], "selection": selected}])
        self.assertEqual(summary["counts"], {"VALUE": 1, "NOT_OBSERVED": 0})

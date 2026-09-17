import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from energyguide_fields import annual_layout_candidates, label_candidates
from g2_label_selection import select_annual_energy, select_capacity


class LabelSelectionTests(unittest.TestCase):
    def setUp(self):
        source = json.loads((ROOT / "tests/fixtures/energyguide-fields/refrigerator.json").read_text(encoding="utf-8"))
        spans = json.loads((ROOT / "tests/fixtures/energyguide-fields/refrigerator-layout.json").read_text(encoding="utf-8"))["spans"]
        self.candidates = label_candidates("\n".join(source["ocr_raw_texts"]), source["extraction_engine"], source["sha256"])
        self.layout = annual_layout_candidates(spans, source["sha256"])
        # Supplied review context is a test boundary input, not expanded-corpus approval.
        layout = self.layout["annual_layout_candidates"][0]
        proposal = layout["nearest_proposal_raw"]
        self.review = {"pdf_sha256": source["sha256"], "document_count": 1,
                       "all_pages_reviewed": True, "us_panel_verified": True, "page": 0,
                       "caption_detection": layout["caption_detection"],
                       "number_detection": proposal["number_detection"],
                       "unit_detection": proposal["unit_detection"]}

    def test_refrigerator_unique_annual_candidate_is_selected(self):
        selected = select_annual_energy(self.candidates, self.layout, self.review)
        self.assertEqual(selected["observation"]["state"], "VALUE")
        self.assertEqual(selected["observation"]["value"]["amount"], 700.0)
        self.assertEqual(selected["observation"]["value"]["unit"], "kWh/year")

    def test_multiple_annual_candidates_remain_unobserved(self):
        candidates = copy.deepcopy(self.candidates)
        candidates["energy_candidates_raw"].append(copy.deepcopy(candidates["energy_candidates_raw"][0]))
        selected = select_annual_energy(candidates, self.layout, self.review)
        self.assertEqual(selected["observation"]["state"], "NOT_OBSERVED")

    def test_layout_disagreement_remains_unobserved(self):
        layout = copy.deepcopy(self.layout)
        layout["annual_layout_candidates"][0]["nearest_proposal_raw"]["value_raw"] = "701"
        selected = select_annual_energy(self.candidates, layout, self.review)
        self.assertEqual(selected["observation"]["state"], "NOT_OBSERVED")

    def test_pdf_provenance_mismatch_is_rejected(self):
        layout = copy.deepcopy(self.layout)
        layout["pdf_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "provenance"):
            select_annual_energy(self.candidates, layout)

    def test_without_panel_review_never_selects(self):
        self.assertEqual(select_annual_energy(self.candidates, self.layout)["observation"]["state"], "NOT_OBSERVED")

    def test_actual_rf22a4111_cost_candidate_contamination_is_not_selected(self):
        source = json.loads((ROOT / "tests/fixtures/energyguide-fields/rf22a4111-selection-projection.json").read_text(encoding="utf-8"))
        review = dict(self.review, pdf_sha256=source["pdf_sha256"])
        result = select_annual_energy(source["candidates"], source["layout"], review)
        self.assertEqual(result["observation"]["state"], "NOT_OBSERVED")

    def test_nearest_of_multiple_proposals_never_selects(self):
        layout = copy.deepcopy(self.layout)
        layout["annual_layout_candidates"][0]["proposals_raw"].append({"value_raw": "701"})
        self.assertEqual(select_annual_energy(self.candidates, layout, self.review)["observation"]["state"], "NOT_OBSERVED")

    def test_review_must_cover_document_and_panel(self):
        for field, value in (("document_count", 2), ("all_pages_reviewed", False),
                             ("us_panel_verified", False), ("page", 1)):
            review = dict(self.review, **{field: value})
            with self.subTest(field=field):
                self.assertEqual(select_annual_energy(self.candidates, self.layout, review)["observation"]["state"], "NOT_OBSERVED")

    def test_reviewed_detection_mismatch_remains_unobserved(self):
        review = dict(self.review, number_detection=self.review["number_detection"] + 1)
        result = select_annual_energy(self.candidates, self.layout, review)
        self.assertEqual(result["observation"]["state"], "NOT_OBSERVED")

    def capacity_review(self, raw="Capacity: 28.6 Cubic Feet"):
        return {"pdf_sha256": self.candidates["pdf_sha256"], "document_count": 1,
                "all_pages_reviewed": True, "us_panel_verified": True, "page": 0,
                "capacity_detection": 8, "capacity_bbox": [[1, 1], [2, 1], [2, 2], [1, 2]],
                "capacity_text_raw": raw}

    def test_explicit_reviewed_capacity_is_selected_without_using_boilerplate(self):
        candidates = copy.deepcopy(self.candidates)
        candidates["capacity_candidates_raw"] = [
            {"value_raw": "Both cost ranges based on models of similar size capacity.", "line": 1},
            {"value_raw": "Capacity: 28.6 Cubic Feet", "line": 2},
        ]
        selected = select_capacity(candidates, self.capacity_review())
        self.assertEqual(selected["observation"]["value"],
                         {"amount": 28.6, "unit": "Cubic Feet", "raw": "Capacity: 28.6 Cubic Feet"})

    def test_capacity_requires_unique_reviewed_explicit_descriptor(self):
        candidates = copy.deepcopy(self.candidates)
        candidates["capacity_candidates_raw"] = [{"value_raw": "Capacity: 28.6 Cubic Feet", "line": 2}]
        for change in (
            {"capacity_text_raw": "Capacity: 29 Cubic Feet"},
            {"document_count": 2},
            {"capacity_bbox": []},
        ):
            with self.subTest(change=change):
                self.assertEqual(select_capacity(candidates, dict(self.capacity_review(), **change))["observation"]["state"], "NOT_OBSERVED")
        candidates["capacity_candidates_raw"].append({"value_raw": "Capacity: 29 Cubic Feet", "line": 3})
        self.assertEqual(select_capacity(candidates, self.capacity_review())["observation"]["state"], "NOT_OBSERVED")

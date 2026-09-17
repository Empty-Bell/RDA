import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from energyguide_fields import annual_layout_candidates, label_candidates
from g2_label_selection import select_annual_energy


class LabelSelectionTests(unittest.TestCase):
    def setUp(self):
        source = json.loads((ROOT / "tests/fixtures/energyguide-fields/refrigerator.json").read_text(encoding="utf-8"))
        spans = json.loads((ROOT / "tests/fixtures/energyguide-fields/refrigerator-layout.json").read_text(encoding="utf-8"))["spans"]
        self.candidates = label_candidates("\n".join(source["ocr_raw_texts"]), source["extraction_engine"], source["sha256"])
        self.layout = annual_layout_candidates(spans, source["sha256"])

    def test_refrigerator_unique_annual_candidate_is_selected(self):
        selected = select_annual_energy(self.candidates, self.layout)
        self.assertEqual(selected["observation"]["state"], "VALUE")
        self.assertEqual(selected["observation"]["value"]["amount"], 700.0)
        self.assertEqual(selected["observation"]["value"]["unit"], "kWh/year")

    def test_multiple_annual_candidates_remain_unobserved(self):
        candidates = copy.deepcopy(self.candidates)
        candidates["energy_candidates_raw"].append(copy.deepcopy(candidates["energy_candidates_raw"][0]))
        selected = select_annual_energy(candidates, self.layout)
        self.assertEqual(selected["observation"]["state"], "NOT_OBSERVED")

    def test_layout_disagreement_remains_unobserved(self):
        layout = copy.deepcopy(self.layout)
        layout["annual_layout_candidates"][0]["nearest_proposal_raw"]["value_raw"] = "701"
        selected = select_annual_energy(self.candidates, layout)
        self.assertEqual(selected["observation"]["state"], "NOT_OBSERVED")

    def test_pdf_provenance_mismatch_is_rejected(self):
        layout = copy.deepcopy(self.layout)
        layout["pdf_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "provenance"):
            select_annual_energy(self.candidates, layout)

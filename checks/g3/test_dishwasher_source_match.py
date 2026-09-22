from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g3_dishwasher_source_match import build, positional_pattern_matches  # noqa: E402


class DishwasherSourceMatchTests(unittest.TestCase):
    def test_positional_pattern_matches_approved_suffix_normalization(self):
        self.assertTrue(positional_pattern_matches("DW80B70*0US", "DW80B7070US/AA"))
        self.assertTrue(positional_pattern_matches("DW8?B7070USR", "DW80B7070USRAA"))
        self.assertFalse(positional_pattern_matches("DW80B7070UQ*", "DW80B7070USRAA"))

    def test_projects_literal_before_positional_pattern_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            obs = root / "obs"; epa = root / "epa"; out = root / "out"
            obs.mkdir(); epa.mkdir()
            (obs / "sku-document-index.json").write_text(json.dumps({"sku_documents": [
                {"exact_sku": "DW80B7070US/AA"}, {"exact_sku": "DW90F89P0USRAA"},
            ]}), encoding="utf-8")
            (epa / "samsung-current-rows.json").write_text(json.dumps([
                {"pd_id": "literal", "model_number": "DW80B7070US"},
                {"pd_id": "pattern", "model_number": "DW80B70*0US"},
                {"pd_id": "only-pattern", "model_number": "DW90F89P0U*R"},
            ]), encoding="utf-8")
            build(obs, epa, out)
            records = {row["exact_sku"]: row for row in json.loads((out / "match-report.json").read_text())["rows"]}
        self.assertEqual(records["DW80B7070US/AA"]["match_status"], "MATCHED_CURRENT_EPA_ROW")
        self.assertEqual(records["DW80B7070US/AA"]["candidate_pd_ids"], ["literal"])
        self.assertEqual(records["DW90F89P0USRAA"]["match_status"], "MATCHED_CURRENT_EPA_PATTERN_CANDIDATES")
        self.assertEqual(records["DW90F89P0USRAA"]["candidate_pd_ids"], ["only-pattern"])

    def test_unknown_pattern_encoding_prevents_false_absence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            obs = root / "obs"; epa = root / "epa"; out = root / "out"
            obs.mkdir(); epa.mkdir()
            (obs / "sku-document-index.json").write_text(json.dumps({"sku_documents": [{"exact_sku": "DW80B7070US/AA"}]}), encoding="utf-8")
            (epa / "samsung-current-rows.json").write_text(json.dumps([{"pd_id": "unknown", "model_number": "DW80#"}]), encoding="utf-8")
            build(obs, epa, out)
            record = json.loads((out / "match-report.json").read_text())["rows"][0]
        self.assertEqual(record["match_status"], "UNRESOLVED_CURRENT_EPA_PATTERN_ENCODING")


if __name__ == "__main__":
    unittest.main()

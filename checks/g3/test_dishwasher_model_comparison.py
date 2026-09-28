from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g3_dishwasher_model_comparison import build, matches_exact, patterns_overlap  # noqa: E402


class DishwasherModelComparisonTests(unittest.TestCase):
    def test_printed_label_prefix_can_match_with_different_star_count(self):
        package = {"rows": [{"exact_sku": "DW80CG5450SRAA",
            "energyguide_model_patterns_visual_reviewed": [{"value_raw": "DW80CB54******; DW80CG54******"}],
            "epa_candidates_raw": []}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "package.json"; source.write_text(json.dumps(package))
            build(source, root / "out")
            record = json.loads((root / "out" / "model-comparison.json").read_text())["records"][0]
        self.assertEqual(record["pdp_vs_energyguide_model"], "EQUAL")
        self.assertEqual(record["matching_energyguide_patterns"], ["DW80CG54******"])

    def test_preserves_wildcards_and_compares_all_three_sources(self):
        self.assertTrue(matches_exact("DW90F8**0***", "DW90F89P0USRAA"))
        self.assertTrue(patterns_overlap("DW90F8**0***", "DW90F89P0USR"))
        package = {"rows": [{"exact_sku": "DW90F89P0USRAA", "energyguide_model_candidates_raw": [{"value_raw": "DW90F8**0***"}], "epa_candidates_raw": [{"model_number": "DW90F8**0***"}]}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "package.json"; source.write_text(json.dumps(package))
            build(source, root / "out")
            record = json.loads((root / "out" / "model-comparison.json").read_text())["records"][0]
        self.assertEqual(record["pdp_vs_energyguide_model"], "EQUAL")
        self.assertEqual(record["pdp_vs_epa_model"], "EQUAL")
        self.assertEqual(record["energyguide_vs_epa_model"], "EQUAL")

    def test_uses_digest_bound_visual_review_without_overwriting_raw_ocr(self):
        package = {"rows": [{"exact_sku": "DW90H89TETEAA",
            "energyguide_model_candidates_raw": [{"value_raw": "DW90H89TE"}],
            "energyguide_model_patterns_visual_reviewed": [{"value_raw": "DW90H89TE**"}],
            "epa_candidates_raw": [{"model_number": "DW90H89TE**"}]}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "package.json"; source.write_text(json.dumps(package))
            build(source, root / "out")
            record = json.loads((root / "out" / "model-comparison.json").read_text())["records"][0]
        self.assertEqual(record["energyguide_model_patterns_ocr_raw"], ["DW90H89TE"])
        self.assertEqual(record["energyguide_model_patterns_visual_reviewed"], ["DW90H89TE**"])
        self.assertEqual(record["energyguide_model_pattern_source"], "HUMAN_VISUAL_REVIEW")
        self.assertEqual(record["pdp_vs_energyguide_model"], "EQUAL")

    def test_any_matching_label_pattern_passes_and_all_patterns_are_preserved(self):
        package = {"rows": [{"exact_sku": "DW80B7070US/AA",
            "energyguide_model_candidates_raw": [
                {"value_raw": "Models DW80B70**A*"},
                {"value_raw": "DW80B70**U*"},
                {"value_raw": "DW80B60**U*"},
            ], "epa_candidates_raw": []}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "package.json"; source.write_text(json.dumps(package))
            build(source, root / "out")
            record = json.loads((root / "out" / "model-comparison.json").read_text())["records"][0]
        self.assertEqual(record["energyguide_model_patterns_raw"], ["DW80B60**U*", "DW80B70**A*", "DW80B70**U*"])
        self.assertEqual(record["pdp_vs_energyguide_model"], "EQUAL")
        self.assertEqual(record["matching_energyguide_patterns"], ["DW80B70**U*"])

    def test_splits_delimited_patterns_inside_a_single_candidate(self):
        package = {"rows": [{"exact_sku": "DW80B7070US/AA",
            "energyguide_model_candidates_raw": [{"value_raw": "DW80B70**A*; DW80B70**U*, DW80B60**U*"}],
            "epa_candidates_raw": []}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "package.json"; source.write_text(json.dumps(package))
            build(source, root / "out")
            record = json.loads((root / "out" / "model-comparison.json").read_text())["records"][0]
        self.assertEqual(record["pdp_vs_energyguide_model"], "EQUAL")
        self.assertEqual(len(record["energyguide_model_patterns_raw"]), 3)


if __name__ == "__main__":
    unittest.main()

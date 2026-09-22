from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g3_dishwasher_model_comparison import build, matches_exact, patterns_overlap  # noqa: E402


class DishwasherModelComparisonTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

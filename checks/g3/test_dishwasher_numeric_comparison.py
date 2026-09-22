from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g3_dishwasher_numeric_comparison import build  # noqa: E402


class DishwasherNumericComparisonTests(unittest.TestCase):
    def test_compares_annual_energy_and_excludes_capacity_place_settings(self):
        package = {"contract": "G3_DISHWASHER_COMPARISON_PACKAGE_V1", "status": "PASS", "rows": [{
            "exact_sku": "DW80B7070US/AA",
            "pdp_energy_raw": [{"value": "225"}],
            "energyguide_energy_candidates_raw": [{"value_raw": "225", "role": "ANNUAL_CAPTION_CONTEXT"}],
            "epa_candidates_raw": [{"annual_energy_use_kwh_year": "225", "capacity_maximum_number_of_place_settings": "16"}],
        }]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "package.json"; source.write_text(json.dumps(package))
            build(source, root / "out")
            report = json.loads((root / "out" / "numeric-comparison.json").read_text())
        row = report["rows"][0]
        self.assertEqual(report["contract"], "G3_DISHWASHER_NUMERIC_COMPARISON_V2")
        self.assertEqual(row["pdp_vs_energyguide_energy"], "EQUAL")
        self.assertNotIn("pdp_vs_epa_place_settings", row)
        self.assertNotIn("pdp_place_settings", row)


if __name__ == "__main__":
    unittest.main()

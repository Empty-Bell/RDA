import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from epa_family_model_match import include, unique_supported_rows


class FamilyModelMatchTests(unittest.TestCase):
    def row(self, model="DW80CG545*****", energy="239", **changes):
        return {"pd_id": "2453103", "brand_name": "Samsung", "model_number": model,
                "markets": "United States, Canada", "date_certified": "2023-04-06",
                "annual_energy_use_kwh_year": energy, **changes}

    def test_long_family_prefix_and_independent_energy(self):
        self.assertEqual(include("DW80CG5450SRAA", self.row(), annual_values=["239"],
                                 allow_trailing_star_group=True),
                         "TRAILING_STAR_MODEL_GROUP_AND_ANNUAL_ENERGY")
        self.assertIsNone(include("DW80CG5450SRAA", self.row(), annual_values=["240"],
                                  allow_trailing_star_group=True))

    def test_short_or_conflicting_identity_never_passes(self):
        self.assertIsNone(include("DW80CG5450SRAA", self.row(model="DW*"), annual_values=["239"],
                                  allow_trailing_star_group=True))
        self.assertIsNone(include("DW80CG5450SRAA", self.row(model="DW80CG546*****"),
                                  annual_values=["239"], allow_trailing_star_group=True))
        self.assertIsNone(include("DW80CG5450SRAA", self.row(model="DW80CG54*X***"),
                                  annual_values=["239"], allow_trailing_star_group=True))

    def test_market_date_and_identity_are_required(self):
        for change in ({"markets": "Canada"}, {"date_certified": ""},
                       {"brand_name": "Other"}, {"pd_id": ""}):
            with self.subTest(change=change):
                self.assertIsNone(include("DW80CG5450SRAA", self.row(**change), annual_values=["239"],
                                          allow_trailing_star_group=True))

    def test_strict_refrigerator_pattern_and_conflicting_values(self):
        fridge = self.row(model="RF25C5A01**", energy="643")
        self.assertEqual(include("RF25C5A01SRAA", fridge), "POSITIONAL_PATTERN")
        self.assertIsNone(include("RF25C5A02SRAA", fridge))
        conflict = self.row(model="RF25C5A01**", energy="700", pd_id="99")
        self.assertEqual(unique_supported_rows("RF25C5A01SRAA", [fridge, conflict]), [])


if __name__ == "__main__":
    unittest.main()

import unittest

from scripts.g3_dishwasher_energy_star_assessment import spec


class DishwasherSpecApplicabilityTest(unittest.TestCase):
    def test_missing_field_is_not_explicit_no(self):
        self.assertEqual(spec([])["state"], "NOT_APPLICABLE")
        self.assertEqual(spec([{"name": "Noise", "value": "42 dBA"}])["state"],
                         "NOT_APPLICABLE")

    def test_explicit_no_remains_absent(self):
        self.assertEqual(spec([{"name": "ENERGY STAR Certified", "value": "No"}])["state"],
                         "ABSENT")


if __name__ == "__main__":
    unittest.main()

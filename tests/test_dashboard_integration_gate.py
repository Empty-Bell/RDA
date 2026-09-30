import unittest

from scripts.dashboard_integration_gate import contradictory_annual_finding


class DashboardIntegrationGateTest(unittest.TestCase):
    def test_rejects_annual_mismatch_when_all_sources_agree(self):
        row = {
            "findings": [{"issue_code": "ANNUAL_ENERGY_MISMATCH"}],
            "annual_energy": {"comparison_candidate": "ALL_THREE_SOURCES_HAVE_SAME_EXACT_VALUE"},
        }
        self.assertTrue(contradictory_annual_finding(row))

    def test_accepts_actual_mismatch(self):
        row = {
            "findings": [{"issue_code": "ANNUAL_ENERGY_MISMATCH"}],
            "annual_energy": {"comparison_candidate": "SOURCE_VALUES_DIFFER"},
        }
        self.assertFalse(contradictory_annual_finding(row))


if __name__ == "__main__":
    unittest.main()

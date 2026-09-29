"""Schema differences must not crash the operational report."""

import unittest

from report_projection import describe, projection


class ReportProjectionContractTest(unittest.TestCase):
    def test_string_epa_registration_and_source_status_are_supported(self):
        record = {"family": "레인지", "model": "NSE6DB850212AA", "grade": "PASS",
                  "findings": [], "raw_summary": {"epa_model": "NSE6D*8502**"},
                  "epa_registration": "PRESENT"}
        detail = {"assessment": {"epa_current_registration": "PRESENT"},
                  "source_comparison": "NOT_EVALUATED"}
        row = projection(record, detail, 1)
        self.assertEqual(row["EPA Status"], "PRESENT")
        self.assertIsNone(row["EG Link Status"])
        self.assertIsNone(row["OCR Status"])

    def test_annual_mismatch_description_includes_epa(self):
        values = {"PDP kWh": 259, "OCR kWh": 259, "EPA kWh": 240}
        description = describe(["ANNUAL_ENERGY_MISMATCH"], values)
        self.assertIn("PDP=259; EnergyGuide=259; EPA=240", description)
        self.assertNotIn("assessment=not assessed", description)

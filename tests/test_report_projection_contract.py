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

    def test_washer_label_candidate_is_shown_when_no_canonical_ocr_amount(self):
        record = {"family": "세탁기", "model": "WF45B6300AP/US", "grade": "PASS",
                  "findings": [], "raw_summary": {"pdp_energy": "93 kWh/Year",
                                                  "label_energy": "93", "epa_energy": "93"},
                  "annual_energy": {"source_kwh_values": {"PDP": ["93"]}},
                  "label_urls": ["https://example.com/label.pdf"],
                  "epa_registration": "PRESENT"}
        detail = {"source_comparison": {"ocr_energy": {"state": "NOT_CAPTURED"}}}
        row = projection(record, detail, 1)
        self.assertEqual(row["OCR kWh"], 93)
        self.assertEqual(row["OCR Status"], "VALUE")

    def test_washer_gallons_and_per_cycle_are_not_annual_kwh(self):
        record = {"family": "세탁기", "model": "WW25FG6B34BEA2", "grade": "LOW",
                  "findings": [{"issue_code": "PDP_ANNUAL_ENERGY_MISSING"}],
                  "raw_summary": {"pdp_energy": "Energy Consumption (gallons/year): 2700 gallons · Energy Consumption (per cycle): 2.25 kWh",
                                  "label_energy": "90", "epa_energy": "90"},
                  "annual_energy": {"source_kwh_values": {"PDP": [], "LABEL": ["90"]}}}
        row = projection(record, {"assessment": {}}, 1)
        self.assertIsNone(row["PDP kWh"])
        self.assertIn("PDP annual kWh=not observed", row["Description"])
        self.assertNotIn("2700", row["Description"])
        self.assertNotIn("2.25", row["Description"])

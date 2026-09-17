"""Reports expose reviewed source facts without deriving a compliance result."""

from dataclasses import fields
import copy
import json
from pathlib import Path
import unittest

from regaudit.facts import TYPES
from regaudit.contracts import ContractError
from regaudit.report import summarize_bundle, verify_report_source_observations

ROOT = Path(__file__).resolve().parents[2]


def absent():
    return {"state": "NOT_OBSERVED", "value": None, "error": None}


class ReportSourceObservationTests(unittest.TestCase):
    def test_energyguide_measurements_are_copied_with_evidence_not_interpreted(self):
        bundle = json.loads((ROOT / "fixtures/g1/bundle.json").read_text(encoding="utf-8"))
        observations = {field.name: absent() for field in fields(TYPES["ENERGYGUIDE"])}
        observations.update(
            {
                "document_url": {
                    "state": "VALUE",
                    "value": "https://example.com/label.pdf",
                    "error": None,
                },
                "document_sha256": {
                    "state": "VALUE",
                    "value": bundle["evidence"][0]["sha256"],
                    "error": None,
                },
                "document_status": {"state": "VALUE", "value": "SOURCE_PDF_PARSED", "error": None},
                "label_model_raw": {
                    "state": "VALUE",
                    "value": "RF23D*9600**",
                    "error": None,
                },
                "annual_energy_kwh": {
                    "state": "VALUE",
                    "value": {"amount": 585.0, "unit": "kWh/year", "raw": "585 kWh"},
                    "error": None,
                },
                "capacity": {
                    "state": "VALUE",
                    "value": {
                        "amount": 22.0,
                        "unit": "Cubic Feet",
                        "raw": "Capacity: 22.0 Cubic Feet",
                    },
                    "error": None,
                },
            }
        )
        bundle["facts"].append(
            {
                "fact_id": "f-energyguide",
                "run_id": "synthetic-g1",
                "product_group": "washer",
                "exact_sku": "SYNTHETIC-SKU",
                "kind": "ENERGYGUIDE",
                "observations": observations,
                "evidence_ids": ["e1"],
            }
        )
        before = copy.deepcopy(bundle)
        report = summarize_bundle(bundle)
        source = report["rows"][0]["energyguide_source_observations"]
        self.assertEqual(len(source), 1)
        self.assertEqual(source[0]["annual_energy_kwh"], observations["annual_energy_kwh"])
        self.assertEqual(source[0]["capacity"], observations["capacity"])
        self.assertEqual(source[0]["label_model_raw"], observations["label_model_raw"])
        self.assertEqual(source[0]["evidence_ids"], ["e1"])
        self.assertEqual(report["counts"]["finding_count"], 0)
        self.assertFalse(report["assessment_enabled"])
        verify_report_source_observations(bundle, report)
        report["rows"][0]["energyguide_source_observations"][0]["capacity"]["value"]["amount"] = 99
        with self.assertRaisesRegex(ContractError, "do not replay"):
            verify_report_source_observations(bundle, report)
        self.assertEqual(bundle, before)

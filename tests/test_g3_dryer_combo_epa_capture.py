"""EPA all-in-one washer/dryer capture preserves distinct component quantities."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from scripts import g3_dryer_combo_epa_capture as capture_module
from scripts.g3_dryer_combo_epa_capture import DATASET, REQUIRED


class DryerComboEpaCaptureContract(unittest.TestCase):
    def test_uses_dedicated_combo_dataset(self):
        self.assertEqual(DATASET, "9jai-gs6t")

    def test_requires_washer_and_dryer_energy_fields_separately(self):
        self.assertIn("annual_energy_use_kwh_year", REQUIRED)
        self.assertIn("estimated_annual_energy_use_kwh_yr_for_the_dryer_in_a_combination_all_in_one_washer_dryer", REQUIRED)
        self.assertIn("drum_capacity_for_the_dryer_in_a_combination_all_in_one_washer_dryer", REQUIRED)

    def test_capture_preserves_both_energy_fields_without_collapsing_them(self):
        fixture_path = Path(__file__).parents[1] / "fixtures/epa-routing/combo-metadata.json"
        metadata = json.loads(fixture_path.read_text(encoding="utf-8"))
        row = {field: None for field in (column["fieldName"] for column in metadata["columns"])}
        row.update({"source_row_id": "1001", "pd_id": "123", "brand_name": "SAMSUNG",
                    "model_number": "WDTEST**", "annual_energy_use_kwh_year": "103",
                    "estimated_annual_energy_use_kwh_yr_for_the_dryer_in_a_combination_all_in_one_washer_dryer": "319",
                    "drum_capacity_for_the_dryer_in_a_combination_all_in_one_washer_dryer": "5.3"})

        def fake_fetch(url):
            parsed = urlparse(url)
            if parsed.path.endswith("/api/views/" + DATASET + ".json"):
                return json.dumps(metadata).encode(), "application/json", 200
            params = parse_qs(parsed.query)
            if "$select" in params and params["$select"][0] == "count(*) as row_count":
                return b'[{"row_count":"1"}]', "application/json", 200
            return json.dumps([row]).encode(), "application/json", 200

        with tempfile.TemporaryDirectory() as directory, patch.object(capture_module, "fetch", side_effect=fake_fetch):
            result = capture_module.capture(Path(directory) / "out")
            saved = json.loads((Path(directory) / "out/samsung-current-rows.json").read_text(encoding="utf-8"))[0]
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(saved["annual_energy_use_kwh_year"], "103")
        self.assertEqual(saved["estimated_annual_energy_use_kwh_yr_for_the_dryer_in_a_combination_all_in_one_washer_dryer"], "319")
        self.assertEqual(result["energy_scope"]["annual_energy_use_kwh_year"], "WASHER_COMPONENT")
        self.assertEqual(result["energy_scope"]["estimated_annual_energy_use_kwh_yr_for_the_dryer_in_a_combination_all_in_one_washer_dryer"], "DRYER_COMPONENT")


if __name__ == "__main__":
    unittest.main()

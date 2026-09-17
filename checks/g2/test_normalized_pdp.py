"""Fixture-first contract tests for G2 source normalization wiring."""

import copy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from g2_normalized import normalize_source_pdp
from source_contract import pdp_facts


class NormalizedPdpAdapterTests(unittest.TestCase):
    def setUp(self):
        self.sku = "RF29DB9900QDAA"
        bridge = json.loads(
            (ROOT / "tests/fixtures/refrigerator/bridge-specs-support.json").read_text(
                encoding="utf-8"
            )
        )
        self.specs = pdp_facts(bridge, self.sku)

    def test_saved_bridge_fixture_preserves_measurement_source_values(self):
        result = normalize_source_pdp(self.specs, None)

        self.assertEqual(result["exact_sku"], self.sku)
        self.assertEqual(
            result["claim_channel_collection"], "NOT_COLLECTED_FOR_THIS_PDP_SAMPLE"
        )
        self.assertEqual(
            result["observations"]["pdp_annual_energy_kwh"]["state"], "VALUE"
        )
        self.assertEqual(
            result["observations"]["pdp_capacity"]["state"], "VALUE"
        )
        self.assertEqual(
            result["observations"]["plp_energy_star_claim"]["state"], "NOT_OBSERVED"
        )

    def test_collected_claim_channels_remain_independent(self):
        claims = {
            "exact_sku": self.sku,
            "plp_energy_star_flag_raw": "Y",
            "pdp_structured_energy_star_fields_raw": [{"value": False}],
        }

        result = normalize_source_pdp(self.specs, claims)

        self.assertTrue(result["observations"]["plp_energy_star_claim"]["value"])
        self.assertFalse(
            result["observations"]["pdp_structured_energy_star_claim"]["value"]
        )
        self.assertEqual(result["claim_channel_collection"], "COLLECTED_SOURCE_RECORD")

    def test_cross_sku_claim_record_is_rejected(self):
        claims = {
            "exact_sku": "RF18A5101SR/AA",
            "plp_energy_star_flag_raw": "Y",
            "pdp_structured_energy_star_fields_raw": [],
        }

        with self.assertRaisesRegex(ValueError, "exact_sku"):
            normalize_source_pdp(self.specs, claims)

    def test_recorded_null_flag_is_not_converted_to_false(self):
        claims = {
            "exact_sku": self.sku,
            "plp_energy_star_flag_raw": None,
            "pdp_structured_energy_star_fields_raw": [],
        }

        result = normalize_source_pdp(self.specs, claims)

        observation = result["observations"]["plp_energy_star_claim"]
        self.assertEqual(observation["state"], "NOT_OBSERVED")
        self.assertIsNone(observation["value"])

    def test_invalid_structured_record_is_rejected_before_normalization(self):
        claims = {
            "exact_sku": self.sku,
            "plp_energy_star_flag_raw": "Y",
            "pdp_structured_energy_star_fields_raw": ["not-a-source-field"],
        }

        with self.assertRaisesRegex(ValueError, "structured PDP"):
            normalize_source_pdp(self.specs, claims)

    def test_adapter_does_not_mutate_source_records(self):
        claims = {
            "exact_sku": self.sku,
            "plp_energy_star_flag_raw": "N",
            "pdp_structured_energy_star_fields_raw": [],
        }
        original_specs, original_claims = copy.deepcopy(self.specs), copy.deepcopy(claims)

        normalize_source_pdp(self.specs, claims)

        self.assertEqual(self.specs, original_specs)
        self.assertEqual(claims, original_claims)

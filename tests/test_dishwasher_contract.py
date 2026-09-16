"""Contracts from hosted dishwasher fixtures; counts are snapshot assertions only."""
import copy
import json
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from source_contract import pf_population, pdp_facts

ROOT = Path(__file__).parent / 'fixtures' / 'dishwasher'


class DishwasherContract(unittest.TestCase):
    def setUp(self):
        self.page = json.loads((ROOT / 'pf-page-0.json').read_text(encoding='utf-8'))
        self.bridge = json.loads((ROOT / 'bridge-specs-support.json').read_text(encoding='utf-8'))

    def test_terminal_population_has_variant_provenance(self):
        result = pf_population([self.page])
        self.assertEqual(result['total_groups'], 9)
        self.assertEqual(result['unique_exact_skus'], 21)

    def test_nonterminal_population_fails_even_when_count_matches(self):
        self.page['hasMoreResults'] = True
        with self.assertRaises(ValueError):
            pf_population([self.page])

    def test_exact_target_retains_family_specific_units(self):
        result = pdp_facts(self.bridge, 'DW90F89P0USRAA', family='dishwasher')
        self.assertEqual(result['energy_consumption_raw'][0]['name'], 'Energy Usage (kWh/year)')
        self.assertEqual(result['energy_consumption_raw'][0]['value'], '225')
        self.assertEqual(result['capacity_raw'][0]['name'], 'Place Setting')
        self.assertEqual(result['capacity_raw'][0]['value'], '16')
        self.assertEqual(result['energy_star_spec_claim_raw'][0]['value'], 'Yes')
        self.assertIn('dw90f89p0usraa', result['energyguide_documents'][0]['url'])
        self.assertIsNone(result['energy_star_structured_claim'])

    def test_target_cannot_borrow_sibling_support(self):
        self.bridge['Support'] = [x for x in self.bridge['Support'] if x['modelCode'] != 'DW90F89P0USRAA']
        with self.assertRaises(ValueError):
            pdp_facts(self.bridge, 'DW90F89P0USRAA', family='dishwasher')

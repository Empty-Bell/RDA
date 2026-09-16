"""Contracts from hosted dishwasher fixtures; counts are snapshot assertions only."""
import copy
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_population, pdp_facts, epa_contract

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


class DishwasherEpaContract(unittest.TestCase):
    def setUp(self):
        self.metadata = json.loads((ROOT / 'epa-metadata.projected.json').read_text(encoding='utf-8'))
        self.rows = json.loads((ROOT / 'epa-sample.projected.json').read_text(encoding='utf-8'))

    def test_observed_schema_preserves_units_without_certification_match(self):
        result = epa_contract(self.metadata, self.rows, dataset='q8py-6w3f')
        self.assertEqual(result['certification_matching'], 'NOT_EVALUATED')
        self.assertEqual(self.rows[0]['annual_energy_use_kwh_year'], '234')
        self.assertEqual(self.rows[0]['water_use_gallons_cycle'], '3.00')
        self.assertEqual(self.rows[0]['capacity_maximum_number_of_place_settings'], '15')

    def test_refrigerator_schema_cannot_substitute_for_dishwasher(self):
        for column in self.metadata['columns']:
            if column['fieldName'] == 'date_certified':
                column['fieldName'] = 'date_qualified'
        with self.assertRaises(ValueError):
            epa_contract(self.metadata, self.rows, dataset='q8py-6w3f')

    def test_wrong_dataset_and_empty_sample_are_errors(self):
        with self.assertRaises(ValueError):
            epa_contract(self.metadata, self.rows)
        with self.assertRaises(ValueError):
            epa_contract(self.metadata, [], dataset='q8py-6w3f')

    def test_optional_upc_row_absence_is_not_no_candidate(self):
        for row in self.rows:
            row.pop('upc', None)
        self.assertEqual(epa_contract(self.metadata, self.rows, dataset='q8py-6w3f')['sample_rows'], 3)

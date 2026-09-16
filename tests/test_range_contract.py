"""Observed range EPA-only contracts; no fuel applicability or certification rules."""
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_population, pdp_facts, epa_contract

ROOT = Path(__file__).parent / 'fixtures' / 'range'

class RangeContract(unittest.TestCase):
    def setUp(self):
        self.pages = [json.loads((ROOT / f'pf-page-{i}.json').read_text(encoding='utf-8')) for i in range(2)]
        self.bridge = json.loads((ROOT / 'bridge-specs-support.json').read_text(encoding='utf-8'))
        self.metadata = json.loads((ROOT / 'epa-metadata.projected.json').read_text(encoding='utf-8'))
        self.rows = json.loads((ROOT / 'epa-sample.projected.json').read_text(encoding='utf-8'))

    def test_complete_population_keeps_all_source_variants(self):
        result = pf_population(self.pages)
        self.assertEqual(result['total_groups'], 19)
        self.assertEqual(result['unique_exact_skus'], 58)
        self.assertTrue(any('gas-range' in r['pdp_url'] for r in result['records']))
        self.assertTrue(any('electric-range' in r['pdp_url'] for r in result['records']))

    def test_missing_terminal_page_fails(self):
        with self.assertRaises(ValueError): pf_population(self.pages[:1])

    def test_exact_pdp_fuel_claim_and_oven_capacity_are_distinct(self):
        facts = pdp_facts(self.bridge, 'NSE80H63XRAA', family='range')
        self.assertEqual(facts['fuel_type_raw'][0]['value'], 'Electric')
        self.assertEqual(facts['cooktop_type_raw'][0]['value'], 'Electric')
        self.assertEqual(facts['oven_capacity_raw'][0]['value'], '6.3 cu. ft.')
        self.assertEqual(facts['energy_star_spec_claim_raw'][0]['value'], 'Yes')
        self.assertEqual(facts['energy_consumption_raw'], [])
        self.assertEqual(facts['energyguide_documents'], [])
        self.assertIsNone(facts['energy_star_structured_claim'])

    def test_unknown_sku_cannot_borrow_electric_claim(self):
        with self.assertRaises(ValueError): pdp_facts(self.bridge, 'UNKNOWN', family='range')

    def test_cooking_dataset_sample_is_not_range_candidate_lookup(self):
        result = epa_contract(self.metadata, self.rows, dataset='m6gi-ng33')
        self.assertEqual(result['certification_matching'], 'NOT_EVALUATED')
        self.assertEqual(self.rows[0]['product_type'], 'Cooktop')
        self.assertEqual(self.rows[0]['annual_energy_consumption_kwh_yr'], '189')
        self.assertEqual(self.rows[0]['low_power_mode_energy_consumption_cooking_top_kwh_yr'], '5.00')
        self.assertNotIn('low_power_mode_energy_consumption_oven_kwh_yr', self.rows[0])

    def test_omitted_component_column_is_schema_error(self):
        self.metadata['columns'] = [c for c in self.metadata['columns'] if c['fieldName'] != 'low_power_mode_energy_consumption_oven_kwh_yr']
        with self.assertRaises(ValueError): epa_contract(self.metadata, self.rows, dataset='m6gi-ng33')

    def test_empty_sample_and_commercial_substitution_fail(self):
        with self.assertRaises(ValueError): epa_contract(self.metadata, [], dataset='m6gi-ng33')
        self.metadata['id'] = 'nt9t-yxu3'
        with self.assertRaises(ValueError): epa_contract(self.metadata, self.rows, dataset='m6gi-ng33')

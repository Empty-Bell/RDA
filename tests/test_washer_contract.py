"""Observed washer contracts; no certification or wildcard matching rules."""
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_population, pdp_facts, epa_contract

ROOT = Path(__file__).parent / 'fixtures' / 'washer'

class WasherContract(unittest.TestCase):
    def setUp(self):
        self.pages = [json.loads((ROOT / f'pf-page-{i}.json').read_text(encoding='utf-8')) for i in range(2)]
        self.bridge = json.loads((ROOT / 'bridge-combo.json').read_text(encoding='utf-8'))
        self.metadata = json.loads((ROOT / 'epa-metadata.projected.json').read_text(encoding='utf-8'))
        self.rows = json.loads((ROOT / 'epa-sample.projected.json').read_text(encoding='utf-8'))

    def test_complete_population_preserves_combo_and_standalone_urls(self):
        result = pf_population(self.pages)
        self.assertEqual(result['total_groups'], 18)
        self.assertEqual(result['unique_exact_skus'], 37)
        self.assertTrue(any('/washer-and-dryer-sets/' in r['pdp_url'] for r in result['records']))
        self.assertTrue(any('/us/laundry/washers/' in r['pdp_url'] for r in result['records']))

    def test_missing_second_page_cannot_be_population(self):
        with self.assertRaises(ValueError):
            pf_population(self.pages[:1])

    def test_combo_facts_preserve_washer_label_quantity(self):
        facts = pdp_facts(self.bridge, 'WD90F53AVBUS', family='washer')
        self.assertEqual(facts['energy_consumption_raw'][0]['value'], '103 kWh/year')
        self.assertEqual(facts['capacity_raw'][0]['value'], '5.3')
        self.assertIsNone(facts['energy_star_structured_claim'])

    def test_standalone_sku_cannot_borrow_combo_bridge(self):
        with self.assertRaises(ValueError):
            pdp_facts(self.bridge, 'WF90F53ADSA5', family='washer')

    def test_live_epa_schema_is_not_candidate_lookup(self):
        result = epa_contract(self.metadata, self.rows, dataset='bghd-e2wd')
        self.assertEqual(result['certification_matching'], 'NOT_EVALUATED')
        self.assertIsInstance(self.rows[0]['annual_energy_use_kwh_year'], str)

    def test_dishwasher_date_name_cannot_substitute(self):
        for column in self.metadata['columns']:
            if column['fieldName'] == 'date_qualified':
                column['fieldName'] = 'date_certified'
        with self.assertRaises(ValueError):
            epa_contract(self.metadata, self.rows, dataset='bghd-e2wd')

    def test_annual_water_column_is_required_independently(self):
        self.metadata['columns'] = [c for c in self.metadata['columns'] if c['fieldName'] != 'annual_water_use_gallons_year']
        with self.assertRaises(ValueError):
            epa_contract(self.metadata, self.rows, dataset='bghd-e2wd')

    def test_empty_epa_sample_is_error(self):
        with self.assertRaises(ValueError):
            epa_contract(self.metadata, [], dataset='bghd-e2wd')

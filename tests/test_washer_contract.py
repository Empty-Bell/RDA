"""Observed washer contracts; no certification or wildcard matching rules."""
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_population, pdp_facts, epa_contract, energyguide_ocr_reason

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

    def test_standalone_missing_pdp_energy_stays_unknown(self):
        source = json.loads((ROOT / 'bridge-standalone.json').read_text(encoding='utf-8'))
        facts = pdp_facts(source, 'WF90F53ADSA5', family='washer')
        self.assertEqual(facts['energy_consumption_raw'], [])
        self.assertEqual(facts['capacity_raw'][0]['value'], '5.3')
        self.assertEqual(len(facts['energy_star_spec_claim_raw']), 2)  # Certified and Most Efficient distinct raw claims
        self.assertIn('wf90f53adsa5', facts['energyguide_documents'][0]['url'])

    def test_long_partial_embedded_text_requires_ocr(self):
        observed = json.loads((ROOT / 'partial-text-energyguide.json').read_text(encoding='utf-8'))
        self.assertGreater(len(observed['embedded_text']), 500)
        self.assertEqual(energyguide_ocr_reason(observed['embedded_text']),
                         'MISSING_ENERGY_VALUE_IN_EMBEDDED_TEXT')

    def test_fallback_health_does_not_choose_energy_value(self):
        self.assertEqual(energyguide_ocr_reason(' \n'), 'EMPTY_EMBEDDED_TEXT')
        self.assertIsNone(energyguide_ocr_reason('Models TEST*; 225 kWh; 307 kWh similar models range'))

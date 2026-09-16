"""Dryer fixtures: combo washer-label energy is not dryer energy."""
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_population, pdp_facts, epa_contract

ROOT = Path(__file__).parent / 'fixtures' / 'dryer'

class DryerContract(unittest.TestCase):
    def setUp(self):
        self.pages=[json.loads((ROOT/f'pf-page-{i}.json').read_text(encoding='utf-8')) for i in range(2)]
        self.bridge=json.loads((ROOT/'bridge-combo.json').read_text(encoding='utf-8'))
        self.metadata=json.loads((ROOT/'epa-metadata.projected.json').read_text(encoding='utf-8'))
        self.rows=json.loads((ROOT/'epa-sample.projected.json').read_text(encoding='utf-8'))

    def test_listing_keeps_combo_and_standalone(self):
        result=pf_population(self.pages)
        self.assertEqual(result['total_groups'],19)
        self.assertEqual(result['unique_exact_skus'],54)
        for path in ('/washer-and-dryer-sets/','/us/laundry/dryers/'):
            self.assertTrue(any(path in r['pdp_url'] for r in result['records']))

    def test_missing_terminal_page_fails(self):
        with self.assertRaises(ValueError): pf_population(self.pages[:1])

    def test_combo_washer_label_not_promoted_to_dryer_energy(self):
        facts=pdp_facts(self.bridge,'WD90F53AVBUS',family='dryer')
        self.assertEqual(facts['energy_consumption_raw'],[])
        self.assertEqual(facts['capacity_raw'],[])
        self.assertTrue(any(x['name']=='Energy Guide Label' and x['value']=='103 kWh/year' for x in facts['spec_fields_raw']))
        self.assertEqual(facts['energy_star_spec_claim_raw'][0]['value'],'Yes')
        self.assertIsNone(facts['energy_star_structured_claim'])

    def test_other_model_cannot_borrow_combo_facts(self):
        with self.assertRaises(ValueError): pdp_facts(self.bridge,'UNKNOWN',family='dryer')

    def test_epa_energy_and_efficiency_remain_separate(self):
        result=epa_contract(self.metadata,self.rows,dataset='t9u7-4d2j')
        self.assertEqual(result['certification_matching'],'NOT_EVALUATED')
        self.assertIsInstance(self.rows[0]['estimated_annual_energy_use_kwh_yr'],str)
        self.assertIsInstance(self.rows[0]['combined_energy_factor_cef'],str)

    def test_missing_fuel_column_is_schema_error(self):
        self.metadata['columns']=[c for c in self.metadata['columns'] if c['fieldName']!='type']
        with self.assertRaises(ValueError): epa_contract(self.metadata,self.rows,dataset='t9u7-4d2j')

    def test_empty_sample_is_not_no_candidate(self):
        with self.assertRaises(ValueError): epa_contract(self.metadata,[],dataset='t9u7-4d2j')

    def test_washer_dataset_cannot_substitute(self):
        with self.assertRaises(ValueError): epa_contract(self.metadata,self.rows,dataset='bghd-e2wd')

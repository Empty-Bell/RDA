"""Observed display fixtures keep size, consumed power and charging output separate."""
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_population, pdp_facts, epa_contract

ROOT=Path(__file__).parent/'fixtures'/'monitor'

class MonitorContract(unittest.TestCase):
    def setUp(self):
        def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
        self.pages=[read(f'pf-page-{i}.json') for i in range(3)]
        self.bridge=read('bridge-specs-support.json')
        self.metadata=read('epa-metadata.projected.json')
        self.rows=read('epa-sample.projected.json')

    def test_observed_terminal_population(self):
        result=pf_population(self.pages)
        self.assertEqual(result['total_groups'],56)
        self.assertEqual(result['unique_exact_skus'],76)

    def test_partial_population_fails(self):
        with self.assertRaises(ValueError): pf_population(self.pages[:2])

    def test_consumption_is_not_charging_output_or_annual_energy(self):
        facts=pdp_facts(self.bridge,'LS40H850TANXZA',family='monitor')
        self.assertEqual(facts['power_consumption_raw'][0]['value'],'340 W')
        self.assertEqual({x['value'] for x in facts['charging_power_raw']},{'15 W','140 W'})
        self.assertEqual(facts['power_supply_raw'][0]['value'],'AC 100 - 240 V')
        self.assertEqual(facts['energy_consumption_raw'],[])
        self.assertIsNone(facts['energy_star_structured_claim'])

    def test_class_size_is_not_active_dimensions(self):
        facts=pdp_facts(self.bridge,'LS40H850TANXZA',family='monitor')
        self.assertEqual(facts['screen_size_class_raw'][0]['value'],'40')
        self.assertEqual([x['value'] for x in facts['active_display_size_raw']],
                         ['36.5 x 15.4 in','926.8 x 391.0 mm'])
        self.assertEqual(facts['resolution_raw'][0]['value'],'WUHD (5120 x 2160)')
        self.assertEqual(facts['capacity_raw'],[])

    def test_unknown_sku_cannot_borrow_facts(self):
        with self.assertRaises(ValueError): pdp_facts(self.bridge,'UNKNOWN',family='monitor')

    def test_signage_sample_without_monitor_energy_is_not_matching(self):
        result=epa_contract(self.metadata,self.rows,dataset='qbg3-d468')
        self.assertEqual(self.rows[0]['display_type'],'Signage Display')
        self.assertNotIn('monitor_total_energy',self.rows[0])
        self.assertEqual(result['certification_matching'],'NOT_EVALUATED')
        column=next(c for c in self.metadata['columns'] if c['fieldName']=='monitor_total_energy')
        self.assertIn('115 Volts (kWh/yr)',column['name'])

    def test_missing_product_type_column_fails(self):
        self.metadata['columns']=[c for c in self.metadata['columns'] if c['fieldName']!='display_type']
        with self.assertRaises(ValueError): epa_contract(self.metadata,self.rows,dataset='qbg3-d468')

    def test_tv_dataset_cannot_substitute(self):
        with self.assertRaises(ValueError): epa_contract(self.metadata,self.rows,dataset='pd96-rr3d')

    def test_empty_epa_sample_is_not_no_candidate(self):
        with self.assertRaises(ValueError): epa_contract(self.metadata,[],dataset='qbg3-d468')

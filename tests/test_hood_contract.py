"""Hood source metrics preserve units and do not establish EPA applicability."""
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_population, pdp_facts, epa_contract

ROOT = Path(__file__).parent / 'fixtures' / 'hood'

class HoodContract(unittest.TestCase):
    def setUp(self):
        self.page=json.loads((ROOT/'pf-page-0.json').read_text(encoding='utf-8'))
        self.bridge=json.loads((ROOT/'bridge-specs-support.json').read_text(encoding='utf-8'))
        self.metadata=json.loads((ROOT/'epa-metadata.projected.json').read_text(encoding='utf-8'))
        self.rows=json.loads((ROOT/'epa-sample.projected.json').read_text(encoding='utf-8'))

    def test_observed_terminal_population(self):
        result=pf_population([self.page])
        self.assertEqual(result['total_groups'],6)
        self.assertEqual(result['unique_exact_skus'],16)

    def test_nonterminal_population_fails(self):
        self.page['hasMoreResults']=True
        with self.assertRaises(ValueError): pf_population([self.page])

    def test_raw_metrics_are_not_annual_energy_or_capacity(self):
        facts=pdp_facts(self.bridge,'NK30CB700WCGAA',family='hood')
        for key,value in [('airflow_raw','390-630'),('noise_raw','50 dBA (1.0 sones)'),
                          ('hood_power_raw','210W'),('hood_type_raw','Wall Mount Chimney'),
                          ('venting_type_raw','Exterior & Recirculating Capable')]:
            self.assertEqual(facts[key][0]['value'],value)
        self.assertEqual(facts['energy_consumption_raw'],[])
        self.assertEqual(facts['capacity_raw'],[])
        self.assertIsNone(facts['energy_star_structured_claim'])

    def test_unknown_sku_cannot_borrow_facts(self):
        with self.assertRaises(ValueError): pdp_facts(self.bridge,'UNKNOWN',family='hood')

    def test_generic_epa_sample_is_not_hood_matching(self):
        result=epa_contract(self.metadata,self.rows,dataset='8dv7-nngq')
        self.assertEqual(result['certification_matching'],'NOT_EVALUATED')
        self.assertEqual(self.rows[0]['unit_type'],'Bathroom/Utility Room')
        self.assertEqual(self.rows[0]['airflow_1_cfm'],'110')
        self.assertEqual(self.rows[0]['efficacy_1_cfm_w'],'4.2')

    def test_missing_product_type_column_fails(self):
        self.metadata['columns']=[c for c in self.metadata['columns'] if c['fieldName']!='unit_type']
        with self.assertRaises(ValueError): epa_contract(self.metadata,self.rows,dataset='8dv7-nngq')

    def test_missing_efficiency_column_fails(self):
        self.metadata['columns']=[c for c in self.metadata['columns'] if c['fieldName']!='efficacy_1_cfm_w']
        with self.assertRaises(ValueError): epa_contract(self.metadata,self.rows,dataset='8dv7-nngq')

    def test_empty_epa_sample_is_not_no_candidate(self):
        with self.assertRaises(ValueError): epa_contract(self.metadata,[],dataset='8dv7-nngq')

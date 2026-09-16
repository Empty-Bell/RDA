"""Cooktop reconnaissance; sample schema access is not fuel applicability or EPA matching."""
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_population, pdp_facts, epa_contract

ROOT = Path(__file__).parent / 'fixtures' / 'cooktop'

class CooktopContract(unittest.TestCase):
    def setUp(self):
        self.page = json.loads((ROOT / 'pf-page-0.json').read_text(encoding='utf-8'))
        self.bridge = json.loads((ROOT / 'bridge-gas.json').read_text(encoding='utf-8'))
        self.metadata = json.loads((ROOT / 'epa-metadata.projected.json').read_text(encoding='utf-8'))
        self.rows = json.loads((ROOT / 'epa-sample.projected.json').read_text(encoding='utf-8'))

    def test_population_keeps_gas_electric_and_induction(self):
        result = pf_population([self.page])
        self.assertEqual(result['total_groups'], 9)
        self.assertEqual(result['unique_exact_skus'], 20)
        for token in ('gas-cooktop', 'electric-cooktop', 'induction-cooktop'):
            self.assertTrue(any(token in r['pdp_url'] for r in result['records']))

    def test_terminal_state_required_even_when_count_matches(self):
        self.page['hasMoreResults'] = True
        with self.assertRaises(ValueError): pf_population([self.page])

    def test_exact_sku_slash_preserved(self):
        facts = pdp_facts(self.bridge, 'NA30N6555TS/AA', family='cooktop')
        self.assertEqual(facts['exact_sku'], 'NA30N6555TS/AA')
        self.assertEqual(facts['cooktop_type_raw'][0]['value'], 'Gas')
        self.assertEqual(facts['energy_consumption_raw'], [])
        self.assertEqual(facts['energyguide_documents'], [])
        self.assertIsNone(facts['energy_star_structured_claim'])

    def test_suffix_cannot_be_silently_removed_for_identity(self):
        with self.assertRaises(ValueError): pdp_facts(self.bridge, 'NA30N6555TS', family='cooktop')

    def test_electric_sku_cannot_borrow_gas_bridge(self):
        with self.assertRaises(ValueError): pdp_facts(self.bridge, 'NZ30K7570RS/AA', family='cooktop')

    def test_epa_shared_dataset_is_only_schema_sample(self):
        result = epa_contract(self.metadata, self.rows, dataset='m6gi-ng33')
        self.assertEqual(result['certification_matching'], 'NOT_EVALUATED')
        self.assertEqual(self.rows[0]['product_type'], 'Cooktop')
        self.assertEqual(self.rows[0]['cooking_top_technology'], 'Induction')

    def test_product_type_schema_column_required(self):
        self.metadata['columns'] = [c for c in self.metadata['columns'] if c['fieldName'] != 'product_type']
        with self.assertRaises(ValueError): epa_contract(self.metadata, self.rows, dataset='m6gi-ng33')

    def test_empty_sample_is_not_no_candidate(self):
        with self.assertRaises(ValueError): epa_contract(self.metadata, [], dataset='m6gi-ng33')

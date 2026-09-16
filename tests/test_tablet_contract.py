"""Hosted Tablet fixtures establish source facts, never certification outcomes."""
import copy
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_population, pdp_facts, epa_contract, computer_selection

ROOT = Path(__file__).parent / 'fixtures' / 'tablet'
TARGET = 'SM-X930NZAAXAR'

class TabletContract(unittest.TestCase):
    def setUp(self):
        self.read = lambda name: json.loads((ROOT / name).read_text(encoding='utf-8'))
        self.page = self.read('pf-page-0.json')
        self.specs = self.read('specs-only.projected.json')
        self.facts = pdp_facts(self.specs, TARGET, family='tablet')

    def test_observed_population(self):
        population = pf_population([self.page])
        self.assertEqual(population['total_groups'], 11)
        self.assertEqual(population['unique_exact_skus'], 50)
        self.assertIn(TARGET, {r['exact_sku'] for r in population['records']})

    def test_unfinished_population_fails(self):
        self.page['hasMoreResults'] = True
        with self.assertRaises(ValueError): pf_population([self.page])

    def test_battery_mah_is_not_wh_or_annual_consumption(self):
        self.assertEqual(self.facts['battery_capacity_mah_raw'][0]['value'], '11600')
        self.assertEqual(self.facts['battery_capacity_raw'], [])
        self.assertEqual(self.facts['energy_consumption_raw'], [])
        self.assertEqual(self.facts['playback_duration_raw'][0]['value'], 'Up to 23')

    def test_configuration_and_connectivity_preserved(self):
        fields = {x['name']: x['value'] for x in self.facts['tablet_configuration_raw']}
        self.assertEqual(fields['Memory_(GB)'], '12')
        self.assertEqual(fields['Storage (GB)'], '256')
        self.assertEqual(fields['OS'], 'Android')
        self.assertEqual(fields['Form Factor'], 'Tablet')
        self.assertEqual(self.facts['connectivity_type_raw'][0]['value'], 'Wi-fi')

    def test_display_geometry_is_not_camera_resolution(self):
        fields = {x['name']: x['value'] for x in self.facts['tablet_display_raw']}
        self.assertEqual(fields['Resolution (Main Display)'], '2960 x 1848 (WQXGA+)')
        self.assertIn('full rectangle', fields['Size (Main_Display)'])
        self.assertNotIn('Rear Camera - Resolution', fields)

    def test_unknown_or_duplicate_sku_fails(self):
        with self.assertRaises(ValueError): pdp_facts(self.specs, 'UNKNOWN', family='tablet')
        target = next(x for x in self.specs['Specs'] if x['modelCode'] == TARGET)
        self.specs['Specs'].append(copy.deepcopy(target))
        with self.assertRaises(ValueError): pdp_facts(self.specs, TARGET, family='tablet')

    def test_missing_support_is_unknown_not_zero_documents(self):
        self.assertEqual(self.facts['document_collection_status'], 'NOT_EVALUATED')
        self.assertIsNone(self.facts['energy_star_structured_claim'])
        with self.assertRaises(ValueError): pdp_facts(self.specs, TARGET, family='monitor')

    def test_selected_configuration_and_purchase_sku_must_agree(self):
        selection = self.read('selected-configuration.projected.json')
        self.assertEqual(computer_selection(selection, TARGET)['exact_sku'], TARGET)
        selection['selected_controls'][0]['sku'] = 'OTHER'
        with self.assertRaises(ValueError): computer_selection(selection, TARGET)

    def test_purchase_control_alone_cannot_prove_configuration(self):
        selection = self.read('selected-configuration.projected.json')
        selection['selected_controls'] = []
        with self.assertRaises(ValueError): computer_selection(selection, TARGET)

    def test_epa_generic_rows_are_not_tablet_candidates(self):
        result = epa_contract(self.read('epa-metadata.projected.json'), self.read('epa-sample.projected.json'), dataset='rxdj-2c88')
        self.assertEqual(result['certification_matching'], 'NOT_EVALUATED')

    def test_missing_type_column_or_wrong_dataset_fails(self):
        metadata = self.read('epa-metadata.projected.json')
        rows = self.read('epa-sample.projected.json')
        with self.assertRaises(ValueError): epa_contract(metadata, rows, dataset='qbg3-d468')
        metadata['columns'] = [c for c in metadata['columns'] if c['fieldName'] != 'type']
        with self.assertRaises(ValueError): epa_contract(metadata, rows, dataset='rxdj-2c88')

    def test_empty_epa_response_is_not_no_candidate(self):
        with self.assertRaises(ValueError): epa_contract(self.read('epa-metadata.projected.json'), [], dataset='rxdj-2c88')

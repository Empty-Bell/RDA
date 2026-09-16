"""Computer listing/schema fixtures do not certify the pending buy-page contract."""
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_population, epa_contract, pdp_facts, project_computer_specs, computer_selection

ROOT=Path(__file__).parent/'fixtures'/'computer'

class ComputerContract(unittest.TestCase):
    def setUp(self):
        def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
        self.page=read('pf-page-0.json')
        self.metadata=read('epa-metadata.projected.json')
        self.rows=read('epa-sample.projected.json')

    def test_observed_galaxy_book_population(self):
        result=pf_population([self.page])
        self.assertEqual(result['total_groups'],11)
        self.assertEqual(result['unique_exact_skus'],23)

    def test_unfinished_population_fails(self):
        self.page['hasMoreResults']=True
        with self.assertRaises(ValueError): pf_population([self.page])

    def test_generic_android_desktop_does_not_establish_tablet_matching(self):
        result=epa_contract(self.metadata,self.rows,dataset='rxdj-2c88')
        self.assertEqual(self.rows[0]['type'],'Integrated Desktop')
        self.assertEqual(self.rows[0]['operating_system_name'],'Android OS')
        self.assertEqual(result['certification_matching'],'NOT_EVALUATED')

    def test_tec_adapter_and_mode_power_remain_distinct(self):
        self.assertEqual(self.rows[0]['tec_of_model_kwh'],'34.0')
        self.assertEqual(self.rows[0]['external_power_supply_rated_power_w'],'65.0')
        self.assertEqual(self.rows[0]['short_idle_watts'],'7.3')
        column=next(c for c in self.metadata['columns'] if c['fieldName']=='tec_of_model_kwh')
        self.assertEqual(column['name'],'TEC of Model (kWh)')

    def test_missing_computer_type_column_fails(self):
        self.metadata['columns']=[c for c in self.metadata['columns'] if c['fieldName']!='type']
        with self.assertRaises(ValueError): epa_contract(self.metadata,self.rows,dataset='rxdj-2c88')

    def test_display_dataset_cannot_substitute(self):
        with self.assertRaises(ValueError): epa_contract(self.metadata,self.rows,dataset='qbg3-d468')

    def test_empty_epa_sample_is_not_no_candidate(self):
        with self.assertRaises(ValueError): epa_contract(self.metadata,[],dataset='rxdj-2c88')

    def test_exact_configuration_battery_and_adapter_not_energy(self):
        data=json.loads((ROOT/'specs-only.projected.json').read_text(encoding='utf-8'))
        facts=pdp_facts(data,'NP960UJH-XG7US',family='computer')
        self.assertEqual(facts['battery_capacity_raw'][0]['value'],'80.20')
        self.assertEqual(facts['adapter_rating_raw'][0]['value'],'140W USB Type-C Adapter')
        self.assertEqual(next(x['value'] for x in facts['computer_configuration_raw'] if x['name']=='Memory Capacity'),'64 GB')
        self.assertEqual(facts['energy_consumption_raw'],[])
        self.assertEqual(facts['document_collection_status'],'NOT_EVALUATED')
        self.assertIsNone(facts['energy_star_structured_claim'])

    def test_first_array_record_cannot_substitute_for_exact_sku(self):
        data=json.loads((ROOT/'specs-only.projected.json').read_text(encoding='utf-8'))
        self.assertNotEqual(data['Specs'][0]['modelCode'],'NP960UJH-XG7US')
        with self.assertRaises(ValueError): pdp_facts(data,'UNKNOWN',family='computer')

    def test_specs_only_does_not_relax_other_family_support_gate(self):
        data=json.loads((ROOT/'specs-only.projected.json').read_text(encoding='utf-8'))
        with self.assertRaises(ValueError): pdp_facts(data,'NP960UJH-XG7US',family='monitor')

    def test_malformed_specs_array_fails(self):
        with self.assertRaises(ValueError): project_computer_specs([{'modelCode':'SKU','fullSpecs':[{}]}])

    def test_selected_sku_and_visible_purchase_control_required(self):
        data=json.loads((ROOT/'selected-configuration.projected.json').read_text(encoding='utf-8'))
        target='NP960UJH-XG7US'
        self.assertEqual(computer_selection(data,target)['exact_sku'],target)
        data['continue_visible']=False
        with self.assertRaises(ValueError): computer_selection(data,target)

    def test_mixed_configuration_cannot_pass_on_one_matching_sku(self):
        data={'selected_controls':[{'sku':'SKU'},{'sku':'OTHER'}],
              'continue_sku':'SKU','continue_visible':True}
        with self.assertRaises(ValueError): computer_selection(data,'SKU')

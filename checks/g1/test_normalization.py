import copy
import json
from pathlib import Path
import unittest
from regaudit.normalization import claim, measurement, normalize_pdp

ROOT=Path(__file__).resolve().parents[2]


class Normalization(unittest.TestCase):
    def test_explicit_flags(self):
        for value,expected in [(True,True),(False,False),('Y',True),('No',False),(' true ',True),('N',False)]:
            with self.subTest(value=value):self.assertIs(claim([value])['observation']['value'],expected)
    def test_absence_does_not_become_false(self):
        for values in ([],[None],[''],['ENERGY STAR Certified'],[0],[1]):
            with self.subTest(values=values):self.assertEqual(claim(values)['observation']['state'],'NOT_OBSERVED')
    def test_conflicting_flags_are_unobserved(self):self.assertEqual(claim(['Y','N'])['reason'],'CONFLICTING_FLAGS_WITHIN_SOURCE_CHANNEL')
    def test_unknown_flag_not_discarded(self):self.assertEqual(claim(['Y','maybe'])['observation']['state'],'NOT_OBSERVED')
    def test_repeated_agreeing_flags(self):self.assertIs(claim(['Yes','Y',True])['observation']['value'],True)
    def test_explicit_annual_unit(self):
        result=measurement([{'name':'Energy Consumption','value':'700 kWh/yr'}],'annual_energy')
        self.assertEqual(result['observation']['value'],{'amount':700.0,'unit':'kWh/year','raw':'Energy Consumption: 700 kWh/yr'})
    def test_zero_energy_preserved(self):self.assertEqual(measurement([{'name':'Energy Consumption','value':'0 kWh/year'}],'annual_energy')['observation']['value']['amount'],0)
    def test_no_implicit_watts_cycle_or_bare_number_conversion(self):
        for value in ('700','208 W','700 kWh/cycle','700 kWh','700 or 800 kWh/year','-1 kWh/year','1,200 kWh/year'):
            with self.subTest(value=value):self.assertEqual(measurement([{'name':'Energy Consumption','value':value}],'annual_energy')['observation']['state'],'NOT_OBSERVED')
    def test_capacity_name_supplies_explicit_unit(self):
        for value in ('29','17.5 cu. ft.'):
            self.assertEqual(measurement([{'name':'Total Capacity (cu. ft.)','value':value}],'capacity')['observation']['value']['unit'],'cu ft')
    def test_capacity_other_unit_not_converted(self):self.assertEqual(measurement([{'name':'Total Capacity (L)','value':'800'}],'capacity')['observation']['state'],'NOT_OBSERVED')
    def test_multiple_measurements_not_arbitrarily_selected(self):
        row={'name':'Energy Consumption','value':'700 kWh/year'}
        self.assertEqual(measurement([row,row],'annual_energy')['observation']['state'],'NOT_OBSERVED')
    def test_numeric_source_type_not_coerced(self):self.assertEqual(measurement([{'name':'Total Capacity (cu. ft.)','value':29}],'capacity')['observation']['state'],'NOT_OBSERVED')
    def test_independent_source_channels(self):
        specs={'exact_sku':'demo','energy_consumption_raw':[],'capacity_raw':[],
               'energy_star_spec_claim_raw':[{'value':'No'}]}
        before=copy.deepcopy(specs);r=normalize_pdp(specs,['Y'],[])
        self.assertIs(r['observations']['plp_energy_star_claim']['value'],True)
        self.assertIs(r['observations']['pdp_spec_energy_star_claim']['value'],False)
        self.assertEqual(r['observations']['pdp_structured_energy_star_claim']['state'],'NOT_OBSERVED')
        self.assertEqual(specs,before)
    def test_actual_claim_fixture(self):
        fixture=json.loads((ROOT/'tests/fixtures/public-claims/refrigerator.json').read_bytes())
        specs=dict(fixture['specs'],energy_consumption_raw=[],capacity_raw=[])
        r=normalize_pdp(specs,[fixture['listing'].get('energyStarFlg')],[])
        self.assertEqual(r['exact_sku'],specs['exact_sku'])
        self.assertEqual(r['channels']['plp_energy_star_claim']['raw'],[fixture['listing'].get('energyStarFlg')])

import copy
import json
from pathlib import Path
import tempfile
import unittest
from regaudit.config import load_configuration
from regaudit.contracts import ContractError, validate_bundle, verify_evidence_files

ROOT=Path(__file__).resolve().parents[2]


class TypedFacts(unittest.TestCase):
    def setUp(self): self.bundle=json.loads((ROOT/'fixtures/g1/typed-bundle.json').read_bytes())
    def rejects(self, index, key, value):
        self.bundle['facts'][index]['observations'][key]={'state':'VALUE','value':value,'error':None}
        with self.assertRaises((ContractError,ValueError,TypeError)): validate_bundle(self.bundle)
    def test_all_three_typed_records(self):
        validate_bundle(self.bundle);verify_evidence_files(self.bundle,ROOT/'fixtures/g1')
        self.assertEqual([f['kind'] for f in self.bundle['facts']],['PDP','ENERGYGUIDE','EPA'])
    def test_unknown_field(self): self.rejects(0,'guessed_claim',True)
    def test_required_field(self):
        del self.bundle['facts'][2]['observations']['markets']
        with self.assertRaises(ContractError): validate_bundle(self.bundle)
    def test_string_claim_not_boolean(self): self.rejects(0,'plp_energy_star_claim','N')
    def test_integer_claim_not_boolean(self): self.rejects(0,'pdp_spec_energy_star_claim',0)
    def test_claim_channels_independent(self):
        self.bundle['facts'][0]['observations']['pdp_spec_energy_star_claim']={'state':'VALUE','value':True,'error':None}
        before=copy.deepcopy(self.bundle);validate_bundle(self.bundle)
        self.assertEqual(self.bundle,before)
        self.assertFalse(self.bundle['facts'][0]['observations']['plp_energy_star_claim']['value'])
    def test_boolean_energy_rejected(self): self.rejects(0,'pdp_annual_energy_kwh',{'amount':False,'unit':'kWh/year','raw':'false'})
    def test_bare_number_has_no_unit(self): self.rejects(0,'pdp_annual_energy_kwh',103)
    def test_wrong_energy_unit_no_conversion(self): self.rejects(0,'pdp_annual_energy_kwh',{'amount':103,'unit':'kWh/cycle','raw':'103 kWh/cycle'})
    def test_missing_raw_measurement(self): self.rejects(0,'pdp_capacity',{'amount':28.6,'unit':'cu ft'})
    def test_capacity_source_unit_preserved(self):
        value={'amount':28.6,'unit':'cu ft','raw':'28.6 cu. ft.'}
        self.bundle['facts'][0]['observations']['pdp_capacity']={'state':'VALUE','value':value,'error':None}
        validate_bundle(self.bundle);self.assertEqual(self.bundle['facts'][0]['observations']['pdp_capacity']['value'],value)
    def test_hash_must_belong_to_fact_evidence(self): self.rejects(1,'document_sha256','f'*64)
    def test_observed_fact_requires_evidence(self):
        self.bundle['facts'][0]['evidence_ids']=[]
        with self.assertRaises(ContractError):validate_bundle(self.bundle)
    def test_market_string_not_array(self): self.rejects(2,'markets','United States')
    def test_missing_upc_does_not_infer_certification(self):
        before=copy.deepcopy(self.bundle);validate_bundle(self.bundle);self.assertEqual(self.bundle,before)
    def test_epa_date_requires_timezone(self): self.rejects(2,'retrieved_at','2026-09-17')
    def test_empty_model_identity(self): self.rejects(2,'model_number','')
    def test_wildcard_and_raw_ocr_preserved(self):
        validate_bundle(self.bundle)
        self.assertEqual(self.bundle['facts'][1]['observations']['label_model_raw']['value'],'SYNTHETIC **')
        self.assertEqual(self.bundle['facts'][1]['observations']['label_model_normalized']['state'],'NOT_OBSERVED')
    def test_zero_ocr_scale(self): self.rejects(1,'ocr_scale',0)
    def test_roi_extent(self): self.rejects(1,'ocr_roi_used',{'page':0,'box':[10,0,5,20],'coordinate_unit':'PDF point'})
    def test_roi_boolean_coordinate(self): self.rejects(1,'ocr_roi_used',{'page':0,'box':[False,0,5,20],'coordinate_unit':'PDF point'})
    def test_null_observed_text(self): self.rejects(1,'embedded_text',None)


class Configuration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'configs').mkdir()
        for p in (ROOT/'configs').glob('*.yaml'):(self.root/'configs'/p.name).write_bytes(p.read_bytes())
        (self.root/'.python-version').write_bytes((ROOT/'.python-version').read_bytes())
    def change(self,name,edit):
        path=self.root/'configs'/(name+'.yaml');d=json.loads(path.read_bytes());edit(d);path.write_text(json.dumps(d),encoding='utf-8')
    def bad(self,name,edit):
        self.change(name,edit)
        with self.assertRaises((ContractError,ValueError,TypeError)):load_configuration(self.root)
    def test_all_configs_valid(self): self.assertEqual(len(load_configuration(self.root)[0]),5)
    def test_unknown_field(self):self.bad('runtime',lambda c:c.update(unknown=True))
    def test_missing_field(self):self.bad('runtime',lambda c:c.pop('llm_enabled'))
    def test_string_false_rejected(self):self.bad('runtime',lambda c:c.update(llm_enabled='false'))
    def test_collection_disabled(self):self.bad('runtime',lambda c:c.update(external_collection_enabled=True))
    def test_runner_rejected(self):self.bad('runtime',lambda c:c.update(hosted_runner='windows-latest'))
    def test_python_lock_consistency(self):self.bad('runtime',lambda c:c.update(audit_python='3.12'))
    def test_duplicate_route(self):self.bad('families',lambda c:c['routes'].append(c['routes'][0]))
    def test_missing_product_group(self):self.bad('families',lambda c:c.update(routes=[r for r in c['routes'] if r['product_group']!='tablet']))
    def test_dataset_format(self):self.bad('families',lambda c:c['routes'][0].update(epa_dataset_id='bad'))
    def test_policy_cannot_be_enabled(self):self.bad('presentation',lambda c:c.update(aggregation_policy='distinct_sku'))
    def test_rules_cannot_be_loaded(self):self.bad('controls',lambda c:c.update(rules=[{'id':'unapproved'}]))
    def test_decision_not_silently_closed(self):self.bad('controls',lambda c:c['open_decisions'].remove('D04'))
    def test_routes_are_not_eligibility(self):self.bad('sources',lambda c:c.update(source_routes_are_eligibility_rules=True))
    def test_config_hash_ignores_formatting(self):
        before=load_configuration(self.root)[1];self.change('sources',lambda c:None)
        self.assertEqual(load_configuration(self.root)[1],before)
    def test_config_hash_changes_with_content(self):
        before=load_configuration(self.root)[1];self.change('sources',lambda c:c.update(contract_version='synthetic-next'))
        self.assertNotEqual(load_configuration(self.root)[1],before)

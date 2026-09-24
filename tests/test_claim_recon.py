import copy
import json
from pathlib import Path
import unittest
from scripts.claim_recon import project_claim_records, claim_facts

class ClaimReconContract(unittest.TestCase):
    def setUp(self):
        self.snapshot = {'target_sku':'SKU', 'product_jsonld':[], 'structured_records':[],
                         'energy_candidates':[{'text':'ENERGY STAR on another product'}]}
        self.listing = {'modelCode':'SKU','energyStarFlg':'Y','ecomFlag':'N','stockFlag':'UNKNOWN'}
        self.specs = {'exact_sku':'SKU','energy_star_spec_claim_raw':[]}

    def facts(self): return claim_facts(self.snapshot,'SKU',self.listing,self.specs)

    def test_claim_sources_are_independent(self):
        result=self.facts()
        self.assertEqual(result['plp_energy_star_flag_raw'],'Y')
        self.assertEqual(result['pdp_spec_energy_star_claim_raw'],[])
        self.assertEqual(result['pdp_structured_claim_status'],'NOT_EVALUATED')
        self.assertEqual(result['rendered_claim_attribution'],'NOT_EVALUATED')

    def test_unrelated_product_cannot_supply_claim_or_availability(self):
        self.snapshot['product_jsonld']=[{'sku':'OTHER','name':'Other','availability':['InStock'],
                                         'additionalProperty':[{'name':'ENERGY STAR','value':'Yes'}]}]
        self.assertEqual(self.facts()['pdp_exact_jsonld_raw'],[])
        self.assertEqual(self.facts()['pdp_structured_claim_status'],'NOT_EVALUATED')

    def test_exact_jsonld_identity_and_raw_flag_preserved(self):
        self.snapshot['product_jsonld']=[{'mpn':'sku','additionalProperty':[{'name':'ENERGY STAR','value':'No'}]}]
        result=self.facts()
        self.assertEqual(result['pdp_jsonld_energy_star_properties_raw'][0]['value'],'No')
        self.assertEqual(result['claim_consistency'],'NOT_EVALUATED')

    def test_product_allowlist_excludes_chat_and_nested_payload(self):
        payload={'Commerce':[{'modelCode':'SKU','energyStarFlg':'N','chat':{'token':'secret'},
                             'energyStarNested':{'unknown':'payload'}}], 'Account':{'secret':'private'}}
        result=project_claim_records(payload)
        self.assertEqual(result,[{'section':'Commerce','modelCode':'SKU',
                                 'energy_star_fields_raw':[{'name':'energyStarFlg','value':'N'}]}])

    def test_unknown_model_does_not_establish_target_flag(self):
        self.snapshot['structured_records']=project_claim_records([{'modelCode':'OTHER','energyStarFlg':'Y'}])
        self.assertEqual(self.facts()['pdp_structured_claim_status'],'NOT_EVALUATED')
        self.assertEqual(project_claim_records({'energyStarFlg':'Y'}),[])

    def test_exact_sku_provenance_required_on_every_surface(self):
        for obj,key in [(self.snapshot,'target_sku'),(self.listing,'modelCode'),(self.specs,'exact_sku')]:
            original=copy.deepcopy(obj);obj[key]='OTHER'
            with self.assertRaises(ValueError): self.facts()
            obj.clear();obj.update(original)

    def test_commerce_raw_values_not_inferred_stock_state(self):
        self.assertEqual(self.facts()['listing_commerce_raw'],{'ecomFlag':'N','stockFlag':'UNKNOWN'})

    def test_missing_collection_is_observation_failure(self):
        del self.snapshot['product_jsonld']
        with self.assertRaises(ValueError): self.facts()

    def test_conflicting_jsonld_identifiers_do_not_establish_current_product(self):
        self.snapshot['product_jsonld']=[{'sku':'SKU','mpn':'OTHER','additionalProperty':[]}]
        self.assertEqual(self.facts()['pdp_exact_jsonld_raw'],[])

    def test_hosted_exact_product_and_distinct_claim_sources(self):
        root=Path(__file__).parent/'fixtures'/'public-claims'
        for family in ('refrigerator','dishwasher','tablet'):
            with self.subTest(family=family):
                fixture=json.loads((root/(family+'.json')).read_text(encoding='utf-8'))
                result=claim_facts(fixture['snapshot'],fixture['listing']['modelCode'],fixture['listing'],fixture['specs'])
                expected=fixture['expected']
                self.assertEqual(result['exact_sku'],expected['exact_sku'])
                self.assertEqual(result['plp_energy_star_flag_raw'],expected['plp_energy_star_flag_raw'])
                self.assertEqual(result['pdp_spec_energy_star_claim_raw'],expected['pdp_spec_energy_star_claim_raw'])
                self.assertEqual(result['claim_consistency'],expected['claim_consistency'])
                self.assertEqual(result['pdp_exact_jsonld_raw'][0]['sku'],result['exact_sku'])
                self.assertEqual(result['plp_energy_star_flag_raw'],'Y')
                self.assertEqual(result['pdp_structured_claim_status'],'NOT_EVALUATED')
                self.assertIn('energy-star-logo-pdp',result['rendered_page_candidates_raw'][0]['src'])

    def test_tablet_logo_candidate_does_not_invent_spec_or_structured_claim(self):
        path=Path(__file__).parent/'fixtures'/'public-claims'/'tablet.json'
        fixture=json.loads(path.read_text(encoding='utf-8'))
        result=claim_facts(fixture['snapshot'],fixture['listing']['modelCode'],fixture['listing'],fixture['specs'])
        self.assertEqual(result['pdp_spec_energy_star_claim_raw'],[])
        self.assertEqual(result['pdp_structured_energy_star_fields_raw'],[])
        self.assertEqual(result['claim_consistency'],'NOT_EVALUATED')

import copy
import json
from pathlib import Path
import unittest
from g2_pdp import coverage, select_sample, verify_identity

ROOT=Path(__file__).resolve().parents[2]


class PdpIdentity(unittest.TestCase):
    def setUp(self):
        self.bridge=json.loads((ROOT/'tests/fixtures/refrigerator/bridge-specs-support.json').read_bytes())
        self.sku=self.bridge['Specs'][0]['modelCode']
        self.url='https://www.samsung.com/us/refrigerators/example-sku-'+self.sku.lower().replace('/','-')+'/'
        self.snapshot={'jsonld_parse_errors':[],'product_jsonld':[{'sku':self.sku,'mpn':None}]}
    def test_exact_identity(self):self.assertEqual(verify_identity(self.sku,self.url,self.snapshot,self.bridge)['exact_sku'],self.sku)
    def test_redirect_other_sku(self):
        with self.assertRaises(ValueError):verify_identity(self.sku,self.url.replace('sku-','sku-other-'),self.snapshot,self.bridge)
    def test_off_domain_redirect(self):
        with self.assertRaises(ValueError):verify_identity(self.sku,self.url.replace('www.samsung.com','example.com'),self.snapshot,self.bridge)
    def test_selected_jsonld_other_variant(self):
        self.snapshot['product_jsonld'][0]['sku']='OTHER'
        with self.assertRaises(ValueError):verify_identity(self.sku,self.url,self.snapshot,self.bridge)
    def test_conflicting_mpn(self):
        self.snapshot['product_jsonld'][0]['mpn']='OTHER'
        with self.assertRaises(ValueError):verify_identity(self.sku,self.url,self.snapshot,self.bridge)
    def test_jsonld_unobserved_is_not_success(self):
        self.snapshot['product_jsonld']=[]
        with self.assertRaises(ValueError):verify_identity(self.sku,self.url,self.snapshot,self.bridge)
    def test_bridge_other_sku(self):
        self.bridge['Specs'][0]['modelCode']='OTHER'
        with self.assertRaises(ValueError):verify_identity(self.sku,self.url,self.snapshot,self.bridge)
    def test_duplicate_specs(self):
        self.bridge['Specs'].append(copy.deepcopy(self.bridge['Specs'][0]))
        with self.assertRaises(ValueError):verify_identity(self.sku,self.url,self.snapshot,self.bridge)
    def test_jsonld_parse_error(self):
        self.snapshot['jsonld_parse_errors']=['invalid']
        with self.assertRaises(ValueError):verify_identity(self.sku,self.url,self.snapshot,self.bridge)
    def test_sku_case_not_fuzzy_merged(self):
        self.snapshot['product_jsonld'][0]['sku']=self.sku.lower()
        with self.assertRaises(ValueError):verify_identity(self.sku,self.url,self.snapshot,self.bridge)


class Coverage(unittest.TestCase):
    def setUp(self):
        self.products=[{'exact_sku':s,'listings':[{'sku_role':role}]} for s,role in [('C','REPRESENTATIVE'),('A','REPRESENTATIVE'),('B','VARIANT'),('D','VARIANT')]]
    def test_sample_includes_representative_and_variant(self):
        sample=select_sample(self.products,'C',3)
        self.assertEqual([p['exact_sku'] for p in sample],['C','A','B'])
    def test_population_smaller_than_bound(self):self.assertEqual(len(select_sample(self.products,'C')),4)
    def test_expanded_bound_keeps_role_priority_and_unique_skus(self):
        products=[{'exact_sku':sku,'listings':[{'sku_role':role}]}
                  for sku,role in [('Z','REPRESENTATIVE'),('B','REPRESENTATIVE'),('C','VARIANT'),
                                   ('A','VARIANT'),('D','VARIANT'),('E','VARIANT'),('F','VARIANT'),
                                   ('G','VARIANT'),('H','VARIANT'),('I','VARIANT'),('J','VARIANT')]]
        sample=select_sample(products,'Z',10)
        self.assertEqual([p['exact_sku'] for p in sample],['Z','B','A','C','D','E','F','G','H','I'])
        self.assertEqual(len({p['exact_sku'] for p in sample}),10)
    def test_limit_validated(self):
        for limit in (0,11,False):
            with self.subTest(limit=limit),self.assertRaises(ValueError):select_sample(self.products,'C',limit)
    def test_success_failure_unattempted_distinct(self):
        r=coverage(self.products,[{'exact_sku':'A','status':'VERIFIED_EXACT_IDENTITY'},{'exact_sku':'B','status':'FAILED'}])
        self.assertEqual(r['counts'],{'VERIFIED_EXACT_IDENTITY':1,'FAILED':1,'NOT_ATTEMPTED':2})
        self.assertEqual(sum(r['counts'].values()),r['population_count'])
    def test_unknown_sku(self):
        with self.assertRaises(ValueError):coverage(self.products,[{'exact_sku':'OTHER','status':'FAILED'}])
    def test_duplicate_result(self):
        r={'exact_sku':'A','status':'FAILED'}
        with self.assertRaises(ValueError):coverage(self.products,[r,r])
    def test_unknown_status(self):
        with self.assertRaises(ValueError):coverage(self.products,[{'exact_sku':'A','status':'PASS'}])
    def test_zero_population_no_false_attempts(self):
        r=coverage([],[]);self.assertEqual(r['population_count'],0);self.assertEqual(r['attempted_count'],0)

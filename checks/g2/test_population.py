import copy
import hashlib
import json
from pathlib import Path
import unittest
from g2_population import population_records
from source_contract import pdp_facts

ROOT=Path(__file__).resolve().parents[2]
PLP='https://www.samsung.com/us/home-appliances/refrigerators/all-refrigerators/'


class Population(unittest.TestCase):
    def setUp(self):self.pages=[p.read_bytes() for p in sorted((ROOT/'tests/fixtures/refrigerator').glob('pf-page-*.json'))]
    def mutate(self,edit):
        pages=[json.loads(raw) for raw in self.pages];edit(pages)
        return [json.dumps(p).encode() for p in pages]
    def test_actual_population_preserves_all_identities_and_hashes(self):
        products,parsed=population_records(self.pages,'fixture-run',PLP)
        expected={v['modelCode'] for raw in self.pages for g in json.loads(raw)['searchResults'] for v in g['groupedProductList']}
        self.assertEqual({p['exact_sku'] for p in products},expected)
        self.assertEqual(len(products),parsed['unique_exact_skus'])
        hashes={hashlib.sha256(raw).hexdigest() for raw in self.pages}
        self.assertTrue(all(l['source_pf_search_hash'] in hashes for p in products for l in p['listings']))
    def test_source_flags_not_coerced(self):
        raw=self.mutate(lambda pages:pages[0]['searchResults'][0]['groupedProductList'][0].update(ecomFlag='N',stockFlag=False))
        products,_=population_records(raw,'run',PLP)
        sku=json.loads(raw[0])['searchResults'][0]['groupedProductList'][0]['modelCode']
        listing=next(p for p in products if p['exact_sku']==sku)['listings'][0]
        self.assertEqual(listing['ecom_flag']['value'],'N');self.assertIs(listing['stock_flag']['value'],False)
    def test_zero_population(self):
        raw=json.dumps({'searchTotalCount':0,'hasMoreResults':False,'searchResults':[]}).encode()
        products,parsed=population_records([raw],'run',PLP)
        self.assertEqual(products,[]);self.assertEqual(parsed['total_groups'],0)
    def test_incomplete_page(self):
        with self.assertRaises(ValueError):population_records(self.pages[:-1],'run',PLP)
    def test_duplicate_boundary_group(self):
        with self.assertRaises(ValueError):population_records(self.pages+[self.pages[-1]],'run',PLP)
    def test_total_drift(self):
        raw=self.mutate(lambda pages:pages[-1].update(searchTotalCount=pages[-1]['searchTotalCount']+1))
        with self.assertRaises(ValueError):population_records(raw,'run',PLP)
    def test_variant_collection_missing(self):
        raw=self.mutate(lambda pages:pages[0]['searchResults'][0].pop('groupedProductList'))
        with self.assertRaises(ValueError):population_records(raw,'run',PLP)
    def test_representative_variant_missing(self):
        raw=self.mutate(lambda pages:pages[0]['searchResults'][0].update(modelCode='MISSING-REP'))
        with self.assertRaises(ValueError):population_records(raw,'run',PLP)
    def test_variant_group_collision(self):
        raw=self.mutate(lambda pages:pages[0]['searchResults'][0]['groupedProductList'][0].update(group_id='OTHER'))
        with self.assertRaises(ValueError):population_records(raw,'run',PLP)
    def test_variant_off_domain_url(self):
        raw=self.mutate(lambda pages:pages[0]['searchResults'][0]['groupedProductList'][0].update(pdpURL='https://example.com/us/product-sku-demo/'))
        with self.assertRaises(ValueError):population_records(raw,'run',PLP)
    def test_target_bridge_sku_required(self):
        bridge=json.loads((ROOT/'tests/fixtures/refrigerator/bridge-specs-support.json').read_bytes())
        with self.assertRaises(ValueError):pdp_facts(bridge,'WRONG-SKU')
    def test_repeated_sku_across_distinct_groups_keeps_provenance(self):
        page=json.loads(self.pages[0]);group=copy.deepcopy(page['searchResults'][0])
        other=copy.deepcopy(group);other['group_id']='other-listing-group'
        for variant in other['groupedProductList']:variant['group_id']=other['group_id']
        raw=json.dumps({'searchTotalCount':2,'hasMoreResults':False,'searchResults':[group,other]}).encode()
        products,_=population_records([raw],'run',PLP)
        self.assertEqual(len(products),len(group['groupedProductList']))
        self.assertTrue(all(len(p['listings'])==2 for p in products))

import copy
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_page, pf_population, pdp_facts, project_bridge

FIXTURE = Path(__file__).parent / 'fixtures/refrigerator/pf-initial.projected.json'


class RefrigeratorPfContract(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text(encoding='utf-8'))

    def test_representative_variant_provenance(self):
        page = pf_page(self.data)
        first = [r for r in page['records'] if r['family_id'] == self.data['searchResults'][0]['group_id']]
        self.assertEqual(len(first), 4)  # fixed historical fixture, never a current population constant
        self.assertEqual(sum(r['sku_role'] == 'REPRESENTATIVE' for r in first), 1)
        self.assertTrue(all(r['representative_sku'] == 'RF29DB9900QDAA' for r in first))

    def test_missing_pagination_is_contract_failure(self):
        del self.data['hasMoreResults']
        with self.assertRaises(ValueError):
            pf_page(self.data)

    def test_missing_variant_collection_is_contract_failure(self):
        del self.data['searchResults'][0]['groupedProductList']
        with self.assertRaises(ValueError):
            pf_page(self.data)

    def test_duplicate_sku_is_contract_failure(self):
        variants = self.data['searchResults'][0]['groupedProductList']
        variants.append(copy.deepcopy(variants[0]))
        with self.assertRaises(ValueError):
            pf_page(self.data)

    def test_redirect_to_listing_is_not_product_url(self):
        self.data['searchResults'][0]['groupedProductList'][0]['pdpURL'] = '/us/refrigerators/all-refrigerators/'
        with self.assertRaises(ValueError):
            pf_page(self.data)

    def test_different_group_is_contract_failure(self):
        self.data['searchResults'][0]['groupedProductList'][0]['group_id'] = 'OTHER_GROUP'
        with self.assertRaises(ValueError):
            pf_page(self.data)


class RefrigeratorPopulationContract(unittest.TestCase):
    def setUp(self):
        root = FIXTURE.parent
        self.pages = [json.loads((root / f'pf-page-{i}.json').read_text(encoding='utf-8')) for i in range(3)]

    def test_full_pagination_separates_groups_and_exact_skus(self):
        result = pf_population(self.pages)
        self.assertEqual([len(p['searchResults']) for p in self.pages], [14, 16, 11])
        self.assertEqual(result['total_groups'], 41)
        self.assertGreater(result['unique_exact_skus'], result['total_groups'])

    def test_missing_last_page_fails(self):
        with self.assertRaises(ValueError):
            pf_population(self.pages[:-1])

    def test_drifted_total_fails(self):
        self.pages[-1]['searchTotalCount'] += 1
        with self.assertRaises(ValueError):
            pf_population(self.pages)


class RefrigeratorPdpContract(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((FIXTURE.parent / 'bridge-specs-support.json').read_text(encoding='utf-8'))

    def test_exact_target_not_first_sibling(self):
        facts = pdp_facts(self.data, 'RF29DB9900QDAA')
        self.assertEqual(facts['energy_consumption_raw'][0]['value'], '700 kWh/yr')
        self.assertEqual(facts['capacity_raw'][0]['value'], '29')
        self.assertIn('rf29db9900qdaa', facts['energyguide_documents'][0]['url'])
        self.assertEqual(facts['energy_star_spec_claim_raw'][0]['value'], 'Yes')
        self.assertIsNone(facts['energy_star_structured_claim'])

    def test_unknown_sku_cannot_borrow_sibling_facts(self):
        with self.assertRaises(ValueError):
            pdp_facts(self.data, 'UNKNOWN')

    def test_missing_support_fails(self):
        del self.data['Support']
        with self.assertRaises(ValueError):
            pdp_facts(self.data, 'RF29DB9900QDAA')

    def test_duplicate_target_fails(self):
        self.data['Specs'].append(copy.deepcopy(self.data['Specs'][-1]))
        with self.assertRaises(ValueError):
            pdp_facts(self.data, 'RF29DB9900QDAA')

    def test_product_allowlist_discards_unrelated_metadata(self):
        self.data['chat'] = {'ipAddress': 'TEST_PRIVATE', 'licenseKey': 'TEST_SECRET'}
        projected = project_bridge(self.data)
        self.assertEqual(set(projected), {'Specs', 'Support'})
        self.assertNotIn('TEST_PRIVATE', json.dumps(projected))
        self.assertNotIn('TEST_SECRET', json.dumps(projected))
        self.assertTrue(all(set(d) <= {'name', 'type', 'url'}
                            for s in projected['Support'] for d in s['supports']))

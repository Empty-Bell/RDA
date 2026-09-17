"""Synthetic boundary mutations of a sanitized observed listing fixture."""
import copy
import json
from pathlib import Path
import unittest
from scripts.source_contract import pf_page, pf_population


class ClosureBoundaries(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / 'tests/fixtures/refrigerator/pf-page-0.json'
        self.page = json.loads(path.read_bytes())

    def test_valid_empty_listing_is_observation_only(self):
        result = pf_population([{'searchTotalCount': 0, 'hasMoreResults': False, 'searchResults': []}])
        self.assertEqual(result['unique_exact_skus'], 0)
        self.assertNotIn('compliance', result)

    def test_error_object_cannot_be_empty_listing(self):
        with self.assertRaises(ValueError): pf_page({'error': 'controlled source error'})

    def test_negative_or_boolean_count_rejected(self):
        for count in (-1, False):
            self.page['searchTotalCount'] = count
            with self.assertRaises(ValueError): pf_page(self.page)

    def test_representative_variant_removal_rejected(self):
        item = self.page['searchResults'][0]
        item['groupedProductList'] = [v for v in item['groupedProductList'] if v['modelCode'] != item['modelCode']]
        with self.assertRaises(ValueError): pf_page(self.page)

    def test_cross_page_group_overlap_rejected(self):
        second = copy.deepcopy(self.page); second['hasMoreResults'] = False
        with self.assertRaises(ValueError): pf_population([self.page, second])

    def test_null_result_list_is_not_empty_listing(self):
        with self.assertRaises(ValueError): pf_page({'searchTotalCount': 0, 'hasMoreResults': False, 'searchResults': None})

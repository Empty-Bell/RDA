import unittest
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from scripts.epa_queries import literal, query_url, decode_rows, row_count, complete_scan, catalog_projection


class EpaQueryBoundaries(unittest.TestCase):
    def row(self, identity='row1'):
        return {'source_row_id':identity,'pd_id':'123','brand_name':'Samsung','model_number':'RF29**'}

    def test_model_literal_keeps_stars_and_escapes_quote_without_like(self):
        condition = 'model_number = ' + literal("RF29**' OR 1=1")
        url = query_url('p5st-her9', {'$where':condition})
        self.assertEqual(parse_qs(urlsplit(url).query)['$where'], ["model_number = 'RF29**'' OR 1=1'"])

    def test_http_errors_html_error_objects_and_malformed_json_never_rows(self):
        for status,kind,body in [(403,'application/json',b'[]'),(429,'application/json',b'[]'),
                                 (503,'application/json',b'[]'),(200,'text/html',b'[]'),
                                 (200,'application/json',b'{"error":true}'),(200,'application/json',b'{'),
                                 (200,'application/json',b'[null]')]:
            with self.assertRaises(ValueError): decode_rows(status,kind,body)

    def test_complete_zero_query_does_not_prove_candidate_absence(self):
        result = complete_scan([decode_rows(200,'application/json',b'[]')],0,0,{}, {},100)
        self.assertEqual(result['candidate_absence'],'NOT_EVALUATED')

    def test_full_terminal_page_requires_explicit_next_empty_page(self):
        with self.assertRaises(ValueError): complete_scan([[self.row()]],1,1,{}, {},1)
        result = complete_scan([[self.row()],[]],1,1,{}, {},1)
        self.assertEqual(result['row_count'],1)

    def test_overlap_truncation_count_and_metadata_changes_fail(self):
        for pages,count,final,before,after in [([[self.row()],[self.row()],[]],2,2,{},{}),
                                             ([[self.row()]],2,2,{},{}),([[self.row()]],1,2,{},{}),
                                             ([[self.row()]],1,1,{'update':1},{'update':2})]:
            with self.assertRaises(ValueError): complete_scan(pages,count,final,before,after,2)

    def test_missing_row_identity_is_not_an_empty_candidate_result(self):
        row = self.row(); del row['model_number']
        with self.assertRaises(ValueError): complete_scan([[row]],1,1,{}, {},100)

    def test_count_malformed_or_missing_does_not_default_to_zero(self):
        for rows in ([],[{}],[{'row_count':'-1'}],[{'row_count':'1.5'}]):
            with self.assertRaises(ValueError): row_count(rows)

    def test_catalog_same_id_on_other_domain_does_not_establish_official_source(self):
        data = {'results':[{'resource':{'id':'p5st-her9','type':'dataset'},'metadata':{'domain':'example.com'}}]}
        with self.assertRaises(ValueError): catalog_projection(data,'p5st-her9')

    def test_catalog_metadata_omits_contacts_and_does_not_certify_models(self):
        data = {'results':[{'resource':{'id':'p5st-her9','type':'dataset'},
                            'metadata':{'domain':'data.energystar.gov','contact':'TEST_CONTACT'},'owner':'TEST_OWNER'}]}
        result = catalog_projection(data,'p5st-her9')
        self.assertNotIn('TEST_CONTACT',json.dumps(result))
        self.assertNotIn('TEST_OWNER',json.dumps(result))
        self.assertEqual(result['current_certification'],'NOT_EVALUATED')

    def fixture(self, dataset):
        return json.loads((Path(__file__).parent / 'fixtures/epa-query' / (dataset + '.json')).read_text(encoding='utf-8'))

    def test_actual_nine_queries_preserve_complete_paging_and_error_boundaries(self):
        paths = list((Path(__file__).parent / 'fixtures/epa-query').glob('*.json'))
        self.assertEqual(len(paths),9)
        for path in paths:
            data = self.fixture(path.stem)
            before = {k:data['metadata_before'][k] for k in ('id','rowsUpdatedAt','viewLastModified','columns')}
            after = {k:data['metadata_after'][k] for k in before}
            result = complete_scan(data['pages'],row_count(data['count_before']),row_count(data['count_after']),before,after,100)
            self.assertEqual(result['certification_matching'],'NOT_EVALUATED',msg=path.stem)
            error = data['controlled_error']
            with self.assertRaises(ValueError):decode_rows(error['status'],error['content_type'],error['body_utf8'])

    def test_actual_empty_fan_brand_query_never_implies_hood_noncertification(self):
        data = self.fixture('8dv7-nngq')
        self.assertEqual(data['pages'],[[]])
        self.assertEqual(row_count(data['count_before']),0)
        self.assertEqual(complete_scan(data['pages'],0,0,{}, {},100)['candidate_absence'],'NOT_EVALUATED')

    def test_actual_monitor_upc_omission_and_nonus_computer_market_remain_raw(self):
        monitor = [r for p in self.fixture('qbg3-d468')['pages'] for r in p]
        self.assertTrue(any(not r.get('upc') for r in monitor))
        computer = [r for p in self.fixture('rxdj-2c88')['pages'] for r in p]
        self.assertTrue(any('United States' not in r.get('markets','') for r in computer))
        self.assertIn('Slate/Tablet',{r.get('type') for r in computer})

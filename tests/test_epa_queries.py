import unittest
from urllib.parse import parse_qs, urlsplit
from scripts.epa_queries import literal, query_url, decode_rows, row_count, complete_scan


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

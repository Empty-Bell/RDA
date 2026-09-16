import json
import unittest
from pathlib import Path
from scripts.energyguide_fields import label_candidates

ROOT=Path(__file__).parent/'fixtures'/'energyguide-fields'

class EnergyGuideCandidates(unittest.TestCase):
    def read(self,name):return json.loads((ROOT/(name+'.json')).read_text(encoding='utf-8'))
    def parse(self,name):
        f=self.read(name)
        return label_candidates('\n'.join(f['ocr_raw_texts']) if f['ocr_raw_texts'] else f['embedded_text'],f['extraction_engine'],f['sha256'])

    def test_observed_annual_numbers_have_caption_context(self):
        for name,value in [('refrigerator','700'),('washer','103'),('tv','390')]:
            result=self.parse(name)
            annual=[c['value_raw'] for c in result['energy_candidates_raw'] if c['role']=='ANNUAL_CAPTION_CONTEXT']
            self.assertIn(value,annual,msg=name)
            self.assertEqual(result['annual_value_selection'],'NOT_EVALUATED')

    def test_bilingual_comparator_values_are_not_automatically_annual(self):
        candidates=self.parse('dishwasher')['energy_candidates_raw']
        for value in ('200','307'):
            c=next(c for c in candidates if c['value_raw']==value)
            self.assertNotEqual(c['role'],'ANNUAL_CAPTION_CONTEXT')
        result=self.parse('dishwasher')
        self.assertEqual(sum(c['value_raw']=='225' for c in result['standalone_numeric_candidates_raw']),2)
        self.assertTrue(result['annual_caption_lines_raw'])
        self.assertEqual(result['annual_value_selection'],'NOT_EVALUATED')

    def test_mixed_ocr_reading_order_does_not_force_long_distance_unit_pair(self):
        result=self.parse('dishwasher')
        self.assertIn({'value_raw':'225','line':28},result['standalone_numeric_candidates_raw'])
        self.assertFalse(any(c['line_start']==28 for c in result['energy_candidates_raw']))

    def test_wildcards_and_capacity_preserved_without_matching(self):
        result=self.parse('refrigerator')
        self.assertIn('RF29DB9900**',[m['value_raw'] for m in result['model_candidates_raw']])
        self.assertIn('28.6',str(result['capacity_candidates_raw']))
        self.assertEqual(result['wildcard_correction'],'NOT_APPLIED')

    def test_partial_embedded_text_does_not_substitute_for_ocr_energy(self):
        fixture=self.read('washer-standalone')
        embedded=label_candidates(fixture['embedded_text'],'PyMuPDF',fixture['sha256'])
        self.assertEqual(embedded['energy_candidates_raw'],[])
        self.assertTrue(self.parse('washer-standalone')['energy_candidates_raw'])

    def test_tariff_and_price_not_kwh_consumption(self):
        result=label_candidates('$32\n13 cents per kWh\n200 kWh\nUses least energy','RapidOCR','a'*64)
        self.assertEqual([c['value_raw'] for c in result['energy_candidates_raw']],['200'])
        self.assertEqual(result['energy_candidates_raw'][0]['role'],'REFERENCE_CONTEXT')

    def test_adjacent_number_unit_lines_keep_raw_indices(self):
        result=label_candidates('700\nkWh\nEstimated Yearly Electricity Use','RapidOCR','a'*64)
        candidate=result['energy_candidates_raw'][0]
        self.assertEqual((candidate['line_start'],candidate['line_end']),(0,1))

    def test_empty_text_and_missing_pdf_hash_fail(self):
        for text,digest in [('', 'a'*64),('700 kWh','missing')]:
            with self.assertRaises(ValueError):label_candidates(text,'RapidOCR',digest)

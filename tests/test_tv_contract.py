"""TV source fixtures; power/cost/energy remain distinct raw quantities."""
import json
import unittest
from pathlib import Path
from scripts.source_contract import pf_population, pdp_facts, epa_contract, energyguide_ocr_reason

ROOT = Path(__file__).parent / 'fixtures' / 'tv'

class TelevisionContract(unittest.TestCase):
    def setUp(self):
        self.pages = [json.loads((ROOT / f'pf-page-{i}.json').read_text(encoding='utf-8')) for i in range(2)]
        self.bridge = json.loads((ROOT / 'bridge-specs-support.json').read_text(encoding='utf-8'))
        self.metadata = json.loads((ROOT / 'epa-metadata.projected.json').read_text(encoding='utf-8'))
        self.rows = json.loads((ROOT / 'epa-sample.projected.json').read_text(encoding='utf-8'))

    def test_population_preserves_screen_size_siblings(self):
        result = pf_population(self.pages)
        self.assertEqual([len(p['searchResults']) for p in self.pages], [21, 20])
        self.assertEqual(result['total_groups'], 41)
        self.assertEqual(result['unique_exact_skus'], 167)

    def test_missing_terminal_page_fails(self):
        with self.assertRaises(ValueError):
            pf_population(self.pages[:1])

    def test_pdp_power_is_not_annual_energy_or_capacity(self):
        facts = pdp_facts(self.bridge, 'MRN75R95HAFXZA', family='tv')
        self.assertEqual(facts['energy_consumption_raw'], [])
        self.assertEqual(facts['capacity_raw'], [])
        self.assertEqual(facts['screen_size_raw'][0]['value'], '75"')
        power = {x['name']: x['value'] for x in facts['power_consumption_raw']}
        self.assertEqual(power['Power Consumption (Typical)'], '208 W')
        self.assertEqual(power['Power Consumption (Max)'], '370 W')
        self.assertEqual(power['Power Consumption (Stand-by)'], '0.5 W')
        self.assertEqual(facts['energy_star_spec_claim_raw'], [])
        self.assertIsNone(facts['energy_star_structured_claim'])

    def test_unknown_sku_cannot_borrow_sample(self):
        with self.assertRaises(ValueError):
            pdp_facts(self.bridge, 'UNKNOWN', family='tv')

    def test_label_raw_cost_range_and_energy_are_preserved(self):
        label = json.loads((ROOT / 'energyguide-observation.json').read_text(encoding='utf-8'))
        self.assertEqual(energyguide_ocr_reason(label['embedded_text']), 'EMPTY_EMBEDDED_TEXT')
        text = ' '.join(label['ocr_raw_texts'])
        self.assertIn('$62', text)
        self.assertIn('$155', text)
        self.assertIn('$32', text)
        self.assertIn('390kWh', text)
        self.assertIsNone(energyguide_ocr_reason(text))
        self.assertEqual(label['field_parser_contract'], 'NOT_EVALUATED')

    def test_epa_power_modes_and_annual_energy_remain_separate(self):
        result = epa_contract(self.metadata, self.rows, dataset='pd96-rr3d')
        self.assertEqual(result['certification_matching'], 'NOT_EVALUATED')
        self.assertEqual(self.rows[0]['reported_annual_energy_consumption_kwh'], '216.87')
        self.assertEqual(self.rows[0]['power_consumption_in_on_mode_watts'], '117.69')

    def test_missing_federal_power_field_is_schema_error(self):
        self.metadata['columns'] = [c for c in self.metadata['columns'] if c['fieldName'] != 'reported_on_mode_power_per_the_federal_test_procedure_watts']
        with self.assertRaises(ValueError):
            epa_contract(self.metadata, self.rows, dataset='pd96-rr3d')

    def test_empty_or_wrong_dataset_is_not_no_candidate(self):
        with self.assertRaises(ValueError):
            epa_contract(self.metadata, [], dataset='pd96-rr3d')
        with self.assertRaises(ValueError):
            epa_contract(self.metadata, self.rows, dataset='bghd-e2wd')

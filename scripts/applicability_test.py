import copy
import json
from pathlib import Path
import unittest
from scripts.applicability_contract import title_version, cfr_sections, criteria_text

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures/applicability'


class AuthorityContract(unittest.TestCase):
    def setUp(self):
        self.xml = (FIXTURES / 'sections.xml').read_bytes()
        self.titles = json.loads((FIXTURES / 'titles.json').read_text())
        self.html = (FIXTURES / 'washer-main.html').read_text(encoding='utf-8')

    def test_actual_sections(self): self.assertEqual(len(cfr_sections(self.xml)), 9)
    def test_missing_section(self):
        with self.assertRaises(ValueError): cfr_sections(self.xml.replace(b'N="305.27"', b'N="999.27"'))
    def test_duplicate_sections(self):
        with self.assertRaises(ValueError): cfr_sections(b'<ROOT>' + self.xml + self.xml + b'</ROOT>')
    def test_xml_entities_rejected(self):
        with self.assertRaises(ValueError): cfr_sections(b'<!DOCTYPE ROOT><ROOT/>')
    def test_malformed_xml_rejected(self):
        with self.assertRaises(Exception): cfr_sections(b'<ROOT>')
    def test_actual_version(self): self.assertEqual(title_version(self.titles)['number'], 16)
    def test_ambiguous_version(self):
        self.titles['titles'] += copy.deepcopy(self.titles['titles'])
        with self.assertRaises(ValueError): title_version(self.titles)
    def test_missing_date(self):
        self.titles['titles'][0].pop('latest_issue_date')
        with self.assertRaises(ValueError): title_version(self.titles)
    def test_actual_criteria_main(self):
        value = criteria_text(self.html, 'Clothes Washers Key Product Criteria')
        self.assertIn('Combination All-in-One Washer-Dryer', value['text'])
    def test_footer_cannot_supply_title(self):
        with self.assertRaises(ValueError): criteria_text('<main>Empty</main><footer>Required</footer>', 'Required')
    def test_script_cannot_supply_title(self):
        with self.assertRaises(ValueError): criteria_text('<main><script>Required</script></main>', 'Required')
    def test_duplicate_main(self):
        with self.assertRaises(ValueError): criteria_text(self.html + self.html, 'Clothes Washers Key Product Criteria')

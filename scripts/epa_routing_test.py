"""Dedicated fixture tests; no browser/OCR dependency or live source calls."""
import copy
import json
from pathlib import Path
import unittest
from scripts.epa_routing_contract import catalog_entries, specification_rows, public_metadata, hood_type_condition, range_hood_rows, identity_select

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures/epa-routing'


class RoutingContract(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((FIXTURES / 'catalog.json').read_text())
        self.html = (FIXTURES / 'specifications.html').read_text()
        self.meta = json.loads((FIXTURES / 'combo-metadata.json').read_text())

    def test_actual_catalog(self):
        self.assertTrue(catalog_entries(self.catalog))

    def test_missing_configured_source(self):
        self.catalog['dataset'] = []
        with self.assertRaises(ValueError): catalog_entries(self.catalog)

    def test_duplicate_source(self):
        self.catalog['dataset'] += copy.deepcopy(self.catalog['dataset'])
        with self.assertRaises(ValueError): catalog_entries(self.catalog)

    def test_inactive_source(self):
        for row in self.catalog['dataset']: row['theme'] = ['Historical Specifications']
        with self.assertRaises(ValueError): catalog_entries(self.catalog)

    def test_actual_specification_rows(self):
        self.assertEqual(len(specification_rows(self.html)), 9)

    def test_specification_status_drift(self):
        with self.assertRaises(ValueError): specification_rows(self.html.replace('In Effect', 'Historical'))

    def test_duplicate_specification_rows(self):
        with self.assertRaises(ValueError): specification_rows(self.html + self.html)

    def test_nonofficial_specification_links(self):
        with self.assertRaises(ValueError): specification_rows(self.html.replace('www.energystar.gov', 'example.com'))

    def test_combo_metadata(self):
        self.assertEqual(public_metadata(self.meta, '9jai-gs6t')['id'], '9jai-gs6t')

    def test_missing_identity_column(self):
        self.meta['columns'] = []
        with self.assertRaises(ValueError): public_metadata(self.meta, '9jai-gs6t')

    def test_wrong_metadata_identity(self):
        with self.assertRaises(ValueError): public_metadata(self.meta, 'bghd-e2wd')

    def test_missing_combo_component_column(self):
        self.meta['columns'] = [c for c in self.meta['columns'] if c['fieldName'] != 'annual_energy_use_kwh_year']
        with self.assertRaises(ValueError): public_metadata(self.meta, '9jai-gs6t')

    def test_actual_fan_field(self):
        meta = json.loads((FIXTURES / 'fan-metadata.json').read_text())
        self.assertEqual(hood_type_condition(meta), "unit_type = 'Range Hood'")

    def test_generic_type_field_cannot_replace_fan_field(self):
        meta = json.loads((FIXTURES / 'fan-metadata.json').read_text())
        for column in meta['columns']:
            if column['fieldName'] == 'unit_type': column['fieldName'] = 'product_type'
        with self.assertRaises(ValueError): hood_type_condition(meta)

    def test_non_hood_or_empty_rows_rejected(self):
        for rows in ([], [{'product_type': 'Range Hood'}], [{'unit_type': 'Bathroom Fan'}]):
            with self.assertRaises(ValueError): range_hood_rows(rows)

    def test_select_uses_explicit_observed_fields(self):
        selection = identity_select(self.meta)
        self.assertTrue(selection.startswith(':id as source_row_id,'))
        self.assertNotIn('*', selection)
        self.assertIn('model_number', selection.split(','))

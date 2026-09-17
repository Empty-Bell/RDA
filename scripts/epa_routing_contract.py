"""Official source observations only; no retail certification decisions."""
from html.parser import HTMLParser
import re
from urllib.parse import urljoin, urlsplit

SPEC_PRODUCTS = ('Consumer Refrigeration', 'Dishwashers', 'Clothes Washers',
                 'Televisions', 'Residential Electric Cooking Products',
                 'Clothes Dryers', 'Fans, Ventilating', 'Displays', 'Computers')
DATASETS = ('p5st-her9', 'q8py-6w3f', 'bghd-e2wd', 'pd96-rr3d', 'm6gi-ng33',
            't9u7-4d2j', '8dv7-nngq', 'qbg3-d468', 'rxdj-2c88')


def hood_type_condition(metadata):
    if metadata.get('id') != '8dv7-nngq' or 'unit_type' not in {c.get('fieldName') for c in metadata.get('columns', [])}:
        raise ValueError('Ventilating Fan unit_type schema missing/drifted')
    return "unit_type = 'Range Hood'"


def range_hood_rows(rows):
    if not rows or any(r.get('unit_type') != 'Range Hood' for r in rows):
        raise ValueError('Range Hood type sample missing/drifted')
    return rows


def identity_select(metadata):
    fields = [c['fieldName'] for c in metadata['columns']
              if re.fullmatch(r'[a-z][a-z0-9_]*', c.get('fieldName', ''))]
    if not {'pd_id', 'brand_name', 'model_number'} <= set(fields):
        raise ValueError('Identity select schema missing')
    return ':id as source_row_id,' + ','.join(fields)


class SpecTable(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.row = None; self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.row = []
        elif tag == 'td' and self.row is not None: self.cell = {'parts': [], 'links': []}
        elif tag == 'a' and self.cell is not None:
            href = dict(attrs).get('href')
            if href: self.cell['links'].append(urljoin('https://www.energystar.gov/products/spec', href))

    def handle_data(self, text):
        if self.cell is not None: self.cell['parts'].append(text)

    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.row.append({'text': ' '.join(' '.join(self.cell['parts']).split()),
                             'links': self.cell['links']}); self.cell = None
        elif tag == 'tr' and self.row is not None:
            if self.row: self.rows.append(self.row)
            self.row = None


def specification_rows(html):
    parser = SpecTable(); parser.feed(html)
    selected = []
    for product in SPEC_PRODUCTS:
        matches = [r for r in parser.rows if len(r) == 6 and r[1]['text'] == product]
        if len(matches) != 1: raise ValueError('Specification row missing/ambiguous: ' + product)
        row = matches[0]
        if row[2]['text'] != 'In Effect' or not re.fullmatch(r'\d+(?:\.\d+)* PDF', row[3]['text']):
            raise ValueError('Specification status/version drift: ' + product)
        if not row[3]['links'] or any(urlsplit(u).hostname != 'www.energystar.gov' for u in row[3]['links']):
            raise ValueError('Official specification URL missing/drifted')
        selected.append({'product': product, 'cells': row})
    return selected


def catalog_entries(data):
    if not isinstance(data, dict) or not isinstance(data.get('dataset'), list):
        raise ValueError('Official DCAT dataset list missing')
    entries = []
    for row in data['dataset']:
        identifier = row.get('identifier', '')
        match = re.fullmatch(r'https://data\.energystar\.gov/api/views/([a-z0-9]{4}-[a-z0-9]{4})', identifier)
        if match:
            entries.append({'dataset_id': match[1], **{k: row.get(k) for k in
                            ('identifier', 'title', 'theme', 'modified', 'description', 'landingPage')},
                            'distribution': [{k: item.get(k) for k in ('mediaType', 'downloadURL', 'describedBy')}
                                             for item in row.get('distribution', [])]})
    for dataset in DATASETS + ('8wj2-sec8',):
        matches = [e for e in entries if e['dataset_id'] == dataset]
        if len(matches) != 1 or 'Active Specifications' not in (matches[0]['theme'] or []):
            raise ValueError('Configured source missing/ambiguous/not advertised active: ' + dataset)
    return entries


def public_metadata(data, dataset):
    if not isinstance(data, dict) or data.get('id') != dataset or not data.get('name'):
        raise ValueError('Source metadata identity missing/drifted')
    columns = data.get('columns')
    if not isinstance(columns, list): raise ValueError('Source columns unavailable')
    fields = {c.get('fieldName') for c in columns}
    if not {'pd_id', 'model_number', 'brand_name', 'markets'} <= fields:
        raise ValueError('Source identity/schema drift')
    if dataset == '9jai-gs6t' and not {'special_type', 'annual_energy_use_kwh_year',
            'estimated_annual_energy_use_kwh_yr_for_the_dryer_in_a_combination_all_in_one_washer_dryer'} <= fields:
        raise ValueError('Combo washer/dryer component schema drift')
    if not isinstance(data.get('rowsUpdatedAt'), int): raise ValueError('Source update metadata missing')
    return {**{k: data.get(k) for k in ('id', 'name', 'description', 'category', 'provenance',
            'publicationStage', 'viewType', 'displayType', 'flags', 'parentViewId', 'rowsUpdatedAt', 'viewLastModified')},
            'columns': [{k: c.get(k) for k in ('fieldName', 'name', 'dataTypeName')} for c in columns]}

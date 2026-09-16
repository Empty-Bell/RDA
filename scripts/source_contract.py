"""Reconnaissance contract assertions; no assessment semantics."""
import re
from urllib.parse import urljoin, urlsplit


def project_bridge(data):
    """Explicit product-only allowlist; never retain chat/analytics/RelatedModels."""
    if not isinstance(data, dict) or not isinstance(data.get('Specs'), list) or not isinstance(data.get('Support'), list):
        raise ValueError('Missing Specs/Support bridge-data contract')
    return {
        'Specs': [{'modelCode': x.get('modelCode'),
                   'fullSpecs': [{'groupName': g.get('groupName'),
                                  'specList': [{'name': s.get('name'), 'value': s.get('value')}
                                               for s in g.get('specList', [])]}
                                 for g in x.get('fullSpecs', [])]} for x in data['Specs']],
        'Support': [{'modelCode': x.get('modelCode'),
                     'supports': [{k: d.get(k) for k in ('name', 'type', 'url')}
                                  for d in x.get('supports', [])
                                  if re.fullmatch(r'energy\s*guide', d.get('name', ''), re.I)]}
                    for x in data['Support']],
    }


def pf_page(data):
    if not isinstance(data, dict):
        raise ValueError('pf_search root must be object')
    total = data.get('searchTotalCount')
    if type(total) is not int or total < 0 or type(data.get('hasMoreResults')) is not bool:
        raise ValueError('Invalid pf_search total/pagination fields')
    products = data.get('searchResults')
    if not isinstance(products, list) or len(products) > total:
        raise ValueError('Invalid pf_search result list')
    records = []
    groups = set()
    for item in products:
        group = item.get('group_id')
        representative = item.get('modelCode')
        if not isinstance(group, str) or not group or group in groups:
            raise ValueError('Missing or duplicate group_id within page')
        groups.add(group)
        variants = item.get('groupedProductList')
        if not isinstance(variants, list) or not variants:
            raise ValueError('Missing groupedProductList; cannot assume no variants')
        if representative not in {v.get('modelCode') for v in variants}:
            raise ValueError('Representative missing from groupedProductList')
        seen = set()
        for variant in variants:
            sku = variant.get('modelCode')
            if not isinstance(sku, str) or not sku or sku in seen:
                raise ValueError('Missing or duplicate variant SKU')
            seen.add(sku)
            if variant.get('group_id') != group:
                raise ValueError('Variant belongs to another group')
            url = urljoin('https://www.samsung.com', variant.get('pdpURL', ''))
            parts = urlsplit(url)
            if parts.hostname != 'www.samsung.com' or '/us/' not in parts.path or '-sku-' not in parts.path:
                raise ValueError('PDP URL not source-backed product URL')
            records.append({'family_id': group, 'representative_sku': representative,
                            'exact_sku': sku, 'sku_role': 'REPRESENTATIVE' if sku == representative else 'VARIANT',
                            'pdp_url': url, 'commerce_status': variant.get('ecomFlag'),
                            'stock_flag': variant.get('stockFlag'),
                            'plp_energy_star_claim_raw': variant.get('energyStarFlg')})
    return {'total_groups': total, 'has_more': data['hasMoreResults'],
            'page_groups': len(groups), 'records': records}


def pdp_facts(data, target, family='refrigerator'):
    names = {
        'refrigerator': ('Energy Consumption', 'Total Capacity (cu. ft.)'),
        'dishwasher': ('Energy Usage (kWh/year)', 'Place Setting'),
    }
    if family not in names:
        raise ValueError('Unknown PDP family contract')
    energy_name, capacity_name = names[family]
    if not isinstance(data, dict) or not isinstance(data.get('Specs'), list) or not isinstance(data.get('Support'), list):
        raise ValueError('Missing Specs/Support bridge-data contract')
    specs = [x for x in data['Specs'] if x.get('modelCode') == target]
    support = [x for x in data['Support'] if x.get('modelCode') == target]
    if len(specs) != 1 or len(support) != 1:
        raise ValueError('Target exact SKU missing or duplicated in Specs/Support')
    if not isinstance(specs[0].get('fullSpecs'), list) or not isinstance(support[0].get('supports'), list):
        raise ValueError('Missing specification/document collection')
    fields = []
    for group in specs[0]['fullSpecs']:
        if not isinstance(group.get('specList'), list):
            raise ValueError('Missing specList')
        for item in group['specList']:
            fields.append({'group': group.get('groupName'), 'name': item.get('name'), 'value': item.get('value')})
    documents = [x for x in support[0]['supports'] if re.fullmatch(r'energy\s*guide', x.get('name', ''), re.I)]
    return {'exact_sku': target,
            'spec_fields_raw': fields,
            'energy_consumption_raw': [x for x in fields if x['name'] == energy_name],
            'capacity_raw': [x for x in fields if x['name'] == capacity_name],
            'energy_star_spec_claim_raw': [x for x in fields if 'ENERGY STAR' in (x['name'] or '')],
            'energy_star_structured_claim': None,
            'energyguide_documents': [{k: x.get(k) for k in ('name', 'type', 'url')} for x in documents]}


def pf_population(pages):
    if not pages:
        raise ValueError('Population pages missing')
    parsed = [pf_page(page) for page in pages]
    total = parsed[0]['total_groups']
    if any(p['total_groups'] != total for p in parsed) or parsed[-1]['has_more']:
        raise ValueError('Population totals drifted or pagination incomplete')
    groups = [x['group_id'] for p in pages for x in p['searchResults']]
    if len(groups) != len(set(groups)) or len(groups) != total:
        raise ValueError('Population has duplicate/missing groups')
    records = [r for page in parsed for r in page['records']]
    return {'total_groups': total, 'unique_exact_skus': len({r['exact_sku'] for r in records}), 'records': records}


def epa_contract(metadata, rows, dataset='p5st-her9'):
    columns = {
        'p5st-her9': {'annual_energy_use_kwh_yr', 'date_qualified'},
        'q8py-6w3f': {'annual_energy_use_kwh_year', 'date_certified',
                      'capacity_maximum_number_of_place_settings', 'water_use_gallons_cycle'},
    }
    if dataset not in columns:
        raise ValueError('Unknown EPA dataset contract')
    required = {'pd_id', 'brand_name', 'model_number', 'upc', 'markets'} | columns[dataset]
    fields = {c.get('fieldName') for c in metadata.get('columns', [])}
    if dataset not in {'p5st-her9', 'q8py-6w3f'} or metadata.get('id') != dataset or not required <= fields:
        raise ValueError('EPA dataset identity or required columns drifted')
    if not isinstance(rows, list) or not rows:
        raise ValueError('EPA sample response unavailable/empty; no absence conclusion')
    for row in rows:
        if not row.get('model_number') or not row.get('brand_name') or not row.get('pd_id'):
            raise ValueError('EPA row missing model/brand/unique ID')
    return {'dataset_id': metadata['id'], 'rows_updated_at': metadata.get('rowsUpdatedAt'),
            'sample_rows': len(rows), 'certification_matching': 'NOT_EVALUATED'}

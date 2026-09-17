"""SoQL extraction boundaries only; no certification or pattern matching."""
import json
import re
from urllib.parse import urlencode

BRAND_WHERE = "upper(brand_name) = 'SAMSUNG'"


def literal(value):
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        raise ValueError('Invalid EPA query literal')
    return "'" + value.replace("'", "''") + "'"


def query_url(dataset, params):
    if not re.fullmatch(r'[a-z0-9]{4}-[a-z0-9]{4}', dataset):
        raise ValueError('Invalid dataset ID')
    return 'https://data.energystar.gov/resource/' + dataset + '.json?' + urlencode(params)


def decode_rows(status, content_type, body):
    if status != 200:
        raise ValueError('EPA HTTP response is not successful')
    if 'json' not in content_type.lower():
        raise ValueError('EPA response is not JSON')
    data = json.loads(body)
    if not isinstance(data, list) or any(not isinstance(r, dict) for r in data):
        raise ValueError('EPA response is not an array of records')
    return data


def row_count(rows):
    if len(rows) != 1 or not re.fullmatch(r'\d+', str(rows[0].get('row_count', ''))):
        raise ValueError('EPA count response malformed')
    return int(rows[0]['row_count'])


def catalog_projection(data, dataset):
    if not isinstance(data, dict) or not isinstance(data.get('results'), list):
        raise ValueError('EPA catalog response malformed')
    entries = []
    for item in data['results']:
        resource = item.get('resource', {})
        metadata = item.get('metadata', {})
        if metadata.get('domain') == 'data.energystar.gov':
            entries.append({'id':resource.get('id'),'name':resource.get('name'),'type':resource.get('type'),
                            'domain':metadata['domain'],'publication_stage':metadata.get('publication_stage')})
    if not any(e['id'] == dataset and e['type'] == 'dataset' for e in entries):
        raise ValueError('Configured dataset not observed in bounded official catalog search')
    return {'entries':entries,'result_set_size_raw':data.get('result_set_size'),
            'configured_dataset_observation':'ADVERTISED_IN_OFFICIAL_DOMAIN',
            'current_certification':'NOT_EVALUATED','cross_version_completeness':'NOT_EVALUATED'}


def complete_scan(pages, expected, final_count, before, after, page_size):
    if before != after or expected != final_count:
        raise ValueError('EPA source changed during scan')
    if not pages or any(len(p) != page_size for p in pages[:-1]) or len(pages[-1]) >= page_size:
        raise ValueError('EPA terminal pagination evidence missing')
    rows = [r for p in pages for r in p]
    if len(rows) != expected:
        raise ValueError('EPA scan count incomplete')
    ids = [r.get('source_row_id') for r in rows]
    if any(not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('EPA page overlap or missing source row identity')
    for r in rows:
        if not all(isinstance(r.get(k), str) and r[k] for k in ('brand_name','model_number','pd_id')):
            raise ValueError('EPA identity fields unavailable')
    return {'query_completeness': 'COMPLETE_OBSERVED_QUERY', 'row_count': len(rows),
            'candidate_absence': 'NOT_EVALUATED', 'certification_matching': 'NOT_EVALUATED',
            'snapshot_atomicity': 'NOT_GUARANTEED_BY_OFFSET_API'}

"""Bounded stdlib-only hosted source routing reconnaissance."""
import hashlib
import json
import os
from pathlib import Path
import urllib.request
import urllib.error
from datetime import datetime, timezone
from epa_routing_contract import DATASETS, catalog_entries, specification_rows, public_metadata, hood_type_condition, range_hood_rows
from epa_queries import BRAND_WHERE, query_url, literal, decode_rows, row_count, complete_scan

OUT = Path('runtime/epa-routing')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'status': 'RUNNING', 'captured_at': datetime.now(timezone.utc).isoformat(),
              'run_id': os.getenv('GITHUB_RUN_ID'), 'git_sha': os.getenv('GITHUB_SHA'),
              'phase_gate': 'NOT_EVALUATED', 'compliance': 'NOT_EVALUATED', 'responses': []}
    def save(name, data):
        (OUT / (name + '.json')).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    save('recon', report)
    def fetch(name, url, preserve=False):
        request = urllib.request.Request(url, headers={'User-Agent': 'RDA-EPA-source-contract/1.0'})
        try:
            response = urllib.request.urlopen(request, timeout=30)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read(8 * 1024 * 1024 + 1)
            record = {'name': name, 'url': url, 'final_url': response.url, 'status': response.status,
                      'content_type': response.headers.get('Content-Type', ''),
                      'size_bytes': len(body), 'body_sha256': hashlib.sha256(body).hexdigest()}
        report['responses'].append(record); save('recon', report)
        if preserve: (OUT / (name + '-response.bin')).write_bytes(body)
        if len(body) > 8 * 1024 * 1024: raise ValueError('Diagnostic response bound exceeded')
        if record['status'] != 200: raise ValueError('Source request failed')
        return record, body
    def json_fetch(name, url, preserve=False):
        record, body = fetch(name, url, preserve)
        if 'json' not in record['content_type'].lower(): raise ValueError('Source response is not JSON')
        return json.loads(body)
    def metadata(ds, suffix):
        result = public_metadata(json_fetch(ds + '-' + suffix, 'https://data.energystar.gov/api/views/' + ds + '.json'), ds)
        save(ds + '-' + suffix, result); return result
    def rows(ds, name, params):
        rec, body = fetch(ds + '-' + name, query_url(ds, params), True)
        return decode_rows(rec['status'], rec['content_type'], body)
    def scan(ds, condition):
        before = metadata(ds, 'before')
        n = row_count(rows(ds, 'count-before', {'$where': condition, '$select': 'count(*) as row_count'}))
        if n > 5000: raise ValueError('Diagnostic query bound exceeded')
        pages = []
        for index in range(51):
            page = rows(ds, 'page-' + str(index), {'$where': condition, '$select': ':id as source_row_id,*',
                        '$order': ':id', '$limit': 100, '$offset': index * 100})
            pages.append(page)
            if len(page) < 100: break
        after_count = row_count(rows(ds, 'count-after', {'$where': condition, '$select': 'count(*) as row_count'}))
        after = metadata(ds, 'after')
        health = complete_scan(pages, n, after_count, before, after, 100)
        result = {'where': condition, 'health': health, 'rows': [r for page in pages for r in page]}
        save(ds + '-scan', result); return result
    try:
        catalog = catalog_entries(json_fetch('dcat', 'https://data.energystar.gov/data.json'))
        save('catalog.projected', catalog)
        rec, body = fetch('specifications', 'https://www.energystar.gov/products/spec')
        if 'html' not in rec['content_type'].lower(): raise ValueError('Specification index is not HTML')
        specs = specification_rows(body.decode('utf-8')); save('specifications.projected', specs)
        for ds in DATASETS:
            meta = metadata(ds, 'route')
            if ds == '8dv7-nngq':
                result = range_hood_rows(rows(ds, 'range-hood-type', {'$where': hood_type_condition(meta), '$limit': 3}))
                save('range-hood-type', result)
        combo = scan('9jai-gs6t', BRAND_WHERE)
        parent = scan('bghd-e2wd', BRAND_WHERE + ' AND special_type = ' + literal('Combination All-in-One Washer/Dryer'))
        def identities(result):
            return sorted((r['pd_id'], r['brand_name'], r['model_number']) for r in result['rows'])
        report['combo_observation'] = {'combo_rows': combo['health']['row_count'],
            'parent_filtered_rows': parent['health']['row_count'],
            'identity_multisets_equal': identities(combo) == identities(parent),
            'relation_scope': 'observed literal Samsung query only; metadata description and flags retained',
            'routing_policy': 'NOT_APPROVED', 'energy_comparison': 'NOT_EVALUATED'}
        report['catalog_observation'] = {'entry_count': len(catalog),
            'configured_sources': 'ADVERTISED_ACTIVE',
            'combo_in_dcat': any(e['dataset_id'] == '9jai-gs6t' for e in catalog),
            'exclusive_active_version': 'NOT_EVALUATED', 'per_model_currency': 'NOT_EVALUATED'}
        report['status'] = 'PASS'; save('recon', report)
        print(json.dumps({k: report[k] for k in ('status', 'combo_observation', 'catalog_observation')}))
    except Exception as error:
        report['status'] = 'FAIL'; report['error_type'] = type(error).__name__; save('recon', report)
        raise


if __name__ == '__main__': main()

"""Stdlib-only authority and laundry-type observations on hosted Ubuntu."""
import gzip
import io
import hashlib
import json
import os
from pathlib import Path
import urllib.request
import urllib.error
from datetime import datetime, timezone
from applicability_contract import title_version, cfr_sections, criteria_text
from epa_queries import query_url, decode_rows, BRAND_WHERE

OUT = Path('runtime/applicability')
BOUND = 8 * 1024 * 1024


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'status': 'RUNNING', 'run_id': os.getenv('GITHUB_RUN_ID'), 'git_sha': os.getenv('GITHUB_SHA'),
              'captured_at': datetime.now(timezone.utc).isoformat(), 'phase_gate': 'NOT_EVALUATED',
              'sku_applicability': 'NOT_EVALUATED', 'compliance': 'NOT_EVALUATED', 'responses': []}
    def save(name, value):
        (OUT / (name + '.json')).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    save('recon', report)
    def fetch(name, url, accept):
        req = urllib.request.Request(url, headers={'User-Agent': 'RDA-official-scope/1.0',
                                                   'Accept': accept, 'Accept-Encoding': 'gzip'})
        try: response = urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as error: response = error
        with response:
            wire = response.read(BOUND + 1)
            encoding = response.headers.get('Content-Encoding', '').lower()
            record = {'name': name, 'url': url, 'status': response.status,
                      'content_type': response.headers.get('Content-Type', ''), 'content_encoding': encoding,
                      'wire_sha256': hashlib.sha256(wire).hexdigest(), 'wire_size': len(wire)}
        report['responses'].append(record); save('recon', report)
        if len(wire) > BOUND: raise ValueError('Wire body bound exceeded')
        if encoding == 'gzip':
            with gzip.GzipFile(fileobj=io.BytesIO(wire)) as stream: body = stream.read(BOUND + 1)
        elif encoding in ('', 'identity'): body = wire
        else: raise ValueError('Unexpected compression')
        record.update({'body_sha256': hashlib.sha256(body).hexdigest(), 'body_size': len(body)}); save('recon', report)
        if len(body) > BOUND: raise ValueError('Decoded body bound exceeded')
        # Preserve public XML/API bytes before parsing. HTML stores public main projection + hash.
        if accept != 'text/html': (OUT / (name + '-response.bin')).write_bytes(body)
        if record['status'] != 200: raise ValueError('Authority request failed')
        if accept.split('/')[-1] not in record['content_type'].lower(): raise ValueError('Authority content-type drift')
        return body
    try:
        version = title_version(json.loads(fetch('ecfr-titles', 'https://www.ecfr.gov/api/versioner/v1/titles.json', 'application/json')))
        report['ecfr_version'] = version; save('recon', report)
        date = version['latest_issue_date']
        url = f'https://www.ecfr.gov/api/versioner/v1/full/{date}/title-16.xml?chapter=I&subchapter=C&part=305'
        sections = cfr_sections(fetch('part305', url, 'application/xml')); save('ftc-sections', sections)
        after = title_version(json.loads(fetch('ecfr-titles-after', 'https://www.ecfr.gov/api/versioner/v1/titles.json', 'application/json')))
        if version != after: raise ValueError('Authority version changed during probe')
        pages = {}
        for product in ('clothes_washers', 'clothes_dryers'):
            title = 'Clothes Washers Key Product Criteria' if product == 'clothes_washers' else 'Clothes Dryers Key Product Criteria'
            url = f'https://www.energystar.gov/products/{product}/key_product_criteria'
            pages[product] = criteria_text(fetch(product, url, 'text/html').decode('utf-8'), title)
        save('laundry-criteria', pages)
        summaries = {}
        for dataset in ('bghd-e2wd', 't9u7-4d2j'):
            params = {'$where': BRAND_WHERE, '$select': 'special_type,count(*) as row_count', '$group': 'special_type',
                      '$order': 'special_type', '$limit': 100}
            body = fetch(dataset + '-types', query_url(dataset, params), 'application/json')
            rows = decode_rows(200, 'application/json', body)
            if len(rows) >= 100 or any(not str(r.get('row_count', '')).isdigit() for r in rows):
                raise ValueError('Type summary unavailable/truncated')
            summaries[dataset] = {'where': BRAND_WHERE, 'group': 'special_type', 'rows': rows,
                                  'scope': 'observed grouped brand query; not SKU routing or atomic snapshot'}
        save('laundry-types', summaries)
        report['status'] = 'PASS'; save('recon', report)
        print(json.dumps({'status': report['status'], 'ecfr_version': version, 'sections': len(sections)}))
    except Exception as error:
        report['status'] = 'FAIL'; report['error_type'] = type(error).__name__; save('recon', report); raise


if __name__ == '__main__': main()

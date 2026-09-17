"""Hosted anonymous EPA brand-query/type/update reconnaissance."""
import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from epa_queries import BRAND_WHERE, literal, query_url, decode_rows, row_count, complete_scan
from source_recon import FAMILIES
from source_contract import epa_contract


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--family', required=True, choices=['refrigerator','dishwasher','washer','tv','range','dryer','hood','monitor','computer'])
    family = parser.parse_args().family
    config = FAMILIES[family]; dataset = config['dataset']
    out = Path('runtime/epa-query') / dataset
    out.mkdir(parents=True, exist_ok=True)
    def save(name, data):
        (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = {'status': 'RUNNING', 'dataset_id': dataset, 'run_id': os.getenv('GITHUB_RUN_ID'),
              'git_sha': os.getenv('GITHUB_SHA'), 'captured_at': datetime.now(timezone.utc).isoformat(),
              'source_routes': [f for f,c in FAMILIES.items() if c['dataset'] == dataset],
              'brand_condition': BRAND_WHERE, 'certification_matching': 'NOT_EVALUATED',
              'candidate_absence': 'NOT_EVALUATED', 'current_certification': 'NOT_EVALUATED',
              'us_market_applicability': 'NOT_EVALUATED', 'responses': []}
    save('recon.json', report)
    def fetch(name, url, metadata=False):
        request = urllib.request.Request(url, headers={'User-Agent':'RDA-EPA-source-contract/1.0','Accept':'application/json'})
        try:
            response = urllib.request.urlopen(request, timeout=30)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read(); status = response.code
            content_type = response.headers.get('Content-Type','')
        record = {'name': name, 'url': url, 'status': status, 'content_type': content_type,
                  'body_sha256': hashlib.sha256(body).hexdigest(), 'size_bytes': len(body)}
        report['responses'].append(record); save('recon.json', report)
        # Product/error responses contain only anonymous public query data. Metadata
        # retains response hash and schema projection, omitting publisher/contact IDs.
        if not metadata:
            (out / (name + '-response.bin')).write_bytes(body)
        return status, content_type, body
    def metadata(name):
        status, kind, body = fetch(name, 'https://data.energystar.gov/api/views/' + dataset + '.json', True)
        assert status == 200 and 'json' in kind.lower(), 'EPA metadata unavailable'
        raw = json.loads(body)
        projected = {k:raw.get(k) for k in ('id','name','rowsUpdatedAt','viewLastModified','publicationDate')}
        projected['columns'] = [{k:c.get(k) for k in ('fieldName','name','dataTypeName')}
                                for c in raw.get('columns',[]) if not c.get('fieldName','').startswith(':')]
        save(name + '.json', projected)
        assert projected['id'] == dataset and projected['name'] == config['dataset_name'], 'EPA identity/name drift'
        assert isinstance(projected['rowsUpdatedAt'], int), 'EPA update metadata unavailable'
        return projected
    def fingerprint(m):
        return {k:m[k] for k in ('id','rowsUpdatedAt','viewLastModified','columns')}
    try:
        before = metadata('metadata-before')
        fields = [c['fieldName'] for c in before['columns'] if re.fullmatch(r'[a-z][a-z0-9_]*',c['fieldName'])]
        selected = [f for f in fields if f in ('pd_id','brand_name','model_number','upc','markets')
                    or re.search(r'type|date|status|withdraw|disqual|additional.*model', f)]
        select = ':id as source_row_id,' + ','.join(selected)
        def rows(name, params):
            result = decode_rows(*fetch(name, query_url(dataset, params)))
            save(name + '.json', result)
            return result
        def scan(name, condition):
            params = {'$where':condition}
            count = row_count(rows(name + '-count-before', {**params,'$select':'count(*) as row_count'}))
            if count > 5000:
                raise ValueError('EPA diagnostic bound exceeded; not a complete query')
            pages = []
            for index in range(51):
                page = rows(name + '-page-' + str(index), {**params,'$select':select,'$order':':id','$limit':100,'$offset':index*100})
                pages.append(page)
                if len(page) < 100:
                    break
            final_count = row_count(rows(name + '-count-after', {**params,'$select':'count(*) as row_count'}))
            return pages, count, final_count
        # Validate established per-dataset columns independently of a possibly empty brand query.
        generic = rows('generic-sample', {'$limit':3,'$order':':id'})
        epa_contract(before,generic,dataset)
        cohort, count, final_count = scan('brand', BRAND_WHERE)
        all_rows = [r for p in cohort for r in p]
        exact = None
        if all_rows:
            model = all_rows[0]['model_number']
            condition = BRAND_WHERE + ' AND model_number = ' + literal(model)
            exact = {'model_literal_raw':model,'where':condition,'scan':scan('exact-model',condition)}
        empty = rows('controlled-empty', {'$where':'1=0','$limit':1})
        assert empty == [], 'Controlled empty query not empty'
        error_status, kind, error_body = fetch('controlled-invalid-query', query_url(dataset, {'$where':'('}))
        assert error_status == 400, 'Expected controlled SoQL syntax rejection not observed'
        try:
            decode_rows(error_status,kind,error_body)
        except ValueError:
            report['controlled_error_boundary'] = 'ERROR_REJECTED_NOT_CANDIDATE_ABSENCE'
        else:
            raise AssertionError('EPA HTTP error accepted as rows')
        after = metadata('metadata-after')
        report['brand_scan'] = complete_scan(cohort,count,final_count,fingerprint(before),fingerprint(after),100)
        if exact:
            report['exact_model_probe'] = {k:exact[k] for k in ('model_literal_raw','where')}
            report['exact_model_probe']['scan'] = complete_scan(*exact['scan'],fingerprint(before),fingerprint(after),100)
        else:
            report['exact_model_probe'] = {'status':'NOT_OBSERVED_NO_BRAND_ROWS'}
        report['raw_field_values'] = {f:sorted({r[f] for r in all_rows if isinstance(r.get(f),str)})
                                    for f in selected if re.search(r'type|market|brand',f)}
        report['omitted_upc_rows'] = sum(not r.get('upc') for r in all_rows)
        report['literal_wildcard_rows'] = sum('*' in r['model_number'] or '?' in r['model_number'] for r in all_rows)
        report['update_metadata'] = {k:before[k] for k in ('rowsUpdatedAt','viewLastModified','publicationDate')}
        report['status'] = 'PASS'
        report['status_meaning'] = 'query extraction contract only; no certification/matching/absence decision'
    except Exception as error:
        report['status'] = 'FAIL'; report['error'] = {'type':type(error).__name__,'message':str(error)}
        save('recon.json', report)
        raise
    save('recon.json', report)
    print(json.dumps({'dataset':dataset,'status':report['status'],'brand_rows':count}))


if __name__ == '__main__':
    main()

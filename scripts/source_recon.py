"""Bounded refrigerator source reconnaissance; no compliance rules."""
import copy
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from runner_probe import safe_url, sanitize
from source_contract import pf_page, pdp_facts, project_bridge

OUT = Path('runtime/source-recon')
FIELDS = ('modelCode', 'modelName', 'id', 'group_id', 'pdpURL', 'consumerUrl',
          'ecomFlag', 'stockFlag', 'energyStarFlg', 'globalFeaturedSortOrder', 'chips')


def save(name, data):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize(data), ensure_ascii=False, indent=2), encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project_pf(data):
    if not isinstance(data, dict) or not isinstance(data.get('searchResults'), list):
        raise ValueError('pf_search response structure changed')
    result = {k: data[k] for k in ('searchTotalCount', 'hasMoreResults') if k in data}
    result['searchResults'] = []
    for item in data['searchResults']:
        row = {k: item[k] for k in FIELDS if k in item}
        row['groupedProductList'] = [{k: v[k] for k in FIELDS if k in v}
                                     for v in item.get('groupedProductList', [])]
        result['searchResults'].append(row)
    return result


def profile(data, prefix='', depth=0):
    """Paths, not full payload, for discovering PDP document/spec contract."""
    if depth > 12:
        return []
    found = []
    if isinstance(data, dict):
        for key, value in data.items():
            path = f'{prefix}.{key}' if prefix else key
            if re.search(r'model|sku|energy|certif|spec|document|download|file|capacity', key, re.I):
                sample = value if isinstance(value, (str, int, float, bool)) or value is None else type(value).__name__
                found.append({'path': path, 'sample': sample if not isinstance(sample, str) else sample[:220]})
            found.extend(profile(value, path, depth + 1))
    elif isinstance(data, list):
        for i, value in enumerate(data[:3]):
            found.extend(profile(value, f'{prefix}[{i}]', depth + 1))
    return found[:250]


def main():
    from playwright.sync_api import sync_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'captured_at': datetime.now(timezone.utc).isoformat(),
              'run_id': os.getenv('GITHUB_RUN_ID'), 'attempt': os.getenv('GITHUB_RUN_ATTEMPT'),
              'git_sha': os.getenv('GITHUB_SHA'), 'scope': 'Refrigerator source contracts only',
              'status': 'RUNNING', 'phase_gate': 'NOT_EVALUATED', 'observations': [], 'checks': []}
    captured_pf = []
    pdp_json = []

    def check(name, fn):
        try:
            report['checks'].append({'name': name, 'status': 'PASS', 'details': fn()})
        except Exception as exc:
            report['checks'].append({'name': name, 'status': 'FAIL', 'error': str(exc).splitlines()[0][:250]})
        save('recon.json', report)
        print(f"{name}: {report['checks'][-1]['status']}", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale='en-US')
        page = context.new_page()

        def observe(response):
            url = response.url
            if 'pf_search' in url:
                try:
                    data = response.json()
                    payload = response.request.post_data_json
                    projected = project_pf(data)
                    name = f'fixtures/pf-{len(captured_pf)}.json'
                    digest = save(name, projected)
                    row = {'url': safe_url(url), 'method': response.request.method,
                           'status': response.status, 'request_body': payload,
                           'fixture': name, 'fixture_sha256': digest,
                           'page_count': len(projected['searchResults'])}
                    report['observations'].append(row)
                    captured_pf.append((data, response.request, payload))
                except Exception as exc:
                    report['observations'].append({'url': safe_url(url), 'status': response.status,
                                                   'error_type': type(exc).__name__})
            elif '/bridge-data?' in url and 'data_type=Specs' in url:
                try:
                    if 'json' not in response.headers.get('content-type', ''):
                        return
                    data = project_bridge(response.json())
                    paths = profile(data)
                    if paths and len(pdp_json) < 12:
                        index = len(pdp_json)
                        digest = save(f'fixtures/pdp-{index}.json', data)
                        pdp_json.append({'url': safe_url(url), 'method': response.request.method,
                                         'request_body': response.request.post_data_json,
                                         'status': response.status, 'paths': paths,
                                         'fixture': f'fixtures/pdp-{index}.json', 'fixture_sha256': digest})
                except Exception:
                    pass

        page.on('response', observe)

        def plp():
            url = 'https://www.samsung.com/us/home-appliances/refrigerators/all-refrigerators/'
            response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(8000)
            assert response and response.status < 400, 'PLP HTTP access failed'
            assert captured_pf, 'pf_search response was not captured'
            text = page.locator('body').inner_text()
            save('plp-dom.json', {'result_text': re.findall(r'.{0,30}\b\d+\s+Results\b.{0,30}', text, re.I),
                                  'buttons': page.get_by_role('button').all_text_contents()[:60]})
            return {'url': safe_url(page.url), 'api_total': captured_pf[0][0].get('searchTotalCount')}

        check('plp_request_contract', plp)

        def pagination():
            assert captured_pf, 'No request to paginate'
            all_products = {}
            rounds = []
            for round_no in range(8):
                for data, _, _ in captured_pf:
                    for product in data['searchResults']:
                        all_products[product['group_id']] = product
                total = captured_pf[0][0]['searchTotalCount']
                rounds.append({'round': round_no, 'groups': len(all_products), 'expected_groups': total})
                if len(all_products) == total:
                    break
                before = len(captured_pf)
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(3500)
                if len(captured_pf) > before:
                    continue  # scrolling may already trigger the next page
                button = page.get_by_role('button', name=re.compile(r'view more|load more|show more', re.I))
                if button.count() and button.first.is_visible():
                    if button.first.is_enabled():
                        button.first.click(timeout=10000)
                else:
                    link = page.get_by_text(re.compile(r'^view more$', re.I))
                    if link.count() and link.first.is_visible():
                        link.first.click(timeout=10000)
                    else:
                        break
                page.wait_for_timeout(3500)
            for data, _, _ in captured_pf:
                pf_page(project_pf(data))
                for product in data['searchResults']:
                    all_products[product['group_id']] = product
            exact = {v['modelCode'] for item in all_products.values()
                     for v in [item] + item.get('groupedProductList', [])}
            rendered = page.locator('[data-modelcode]').evaluate_all('(els) => els.map(e => ({tag:e.tagName, cls:e.className, sku:e.getAttribute("data-modelcode")}))')
            visible_links = page.locator('a[href*="-sku-"]:visible').evaluate_all('(els) => els.map(e => e.href.toUpperCase())')
            supported_reps = {x['modelCode'] for x in all_products.values()
                              if any(x['modelCode'] in link for link in visible_links)}
            save('population-observation.json', {'rounds': rounds, 'groups': len(all_products),
                                                'exact_skus': sorted(exact), 'rendered_candidates': rendered[:200],
                                                'rendered_representative_link_count': len(supported_reps)})
            assert len(all_products) == total, f'Pagination incomplete: {len(all_products)}/{total} groups'
            return {'groups': len(all_products), 'exact_skus': len(exact), 'rounds': rounds,
                    'rendered_representative_link_count': len(supported_reps),
                    'strict_tile_count_gate': 'NOT_EVALUATED'}

        check('pagination_observation', pagination)

        def pdp():
            assert captured_pf, 'No population source'
            product = captured_pf[0][0]['searchResults'][0]
            target = product['modelCode']
            url = urljoin('https://www.samsung.com', product['pdpURL'])
            response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(10000)
            text = page.locator('body').inner_text()
            html = page.content()
            links = page.locator('a[href]').evaluate_all('(els) => els.map(e => ({text:e.textContent,url:e.href}))')
            documents = [x for x in links if re.search(r'energy\s*guide', x['text'] or '', re.I)]
            bridge_snippets = re.findall(r'.{0,100}bridge_data.{0,150}', html, re.I)
            save('pdp-observation.json', {'target_sku': target, 'source_url': url, 'final_url': safe_url(page.url),
                                         'http_status': response.status if response else None,
                                         'rendered_target_present': target.lower() in text.lower(),
                                         'energyguide_links': documents, 'bridge_snippets': bridge_snippets[:8],
                                         'json_endpoints': pdp_json})
            assert response and response.status < 400, 'PDP HTTP access failed'
            assert target.lower() in text.lower(), 'Exact SKU not supported by rendered PDP text'
            assert pdp_json, 'Specs/Support bridge-data endpoint was not observed'
            source = json.loads((OUT / pdp_json[0]['fixture']).read_text(encoding='utf-8'))
            facts = pdp_facts(source, target)
            save('pdp-facts.json', facts)
            assert facts['energyguide_documents'], 'No EnergyGuide metadata in target Support record'
            document = facts['energyguide_documents'][0]
            pdf = context.request.get(document['url'], timeout=30000)
            raw = pdf.body()
            assert pdf.status == 200 and raw.startswith(b'%PDF-'), 'EnergyGuide response is not a valid PDF'
            import pymupdf
            parsed = pymupdf.open(stream=raw, filetype='pdf')
            extracted = '\n'.join(p.get_text() for p in parsed)
            (OUT / 'energyguide-original.pdf').write_bytes(raw)
            save('energyguide-observation.json', {'requested_url': document['url'], 'final_url': safe_url(pdf.url),
                                                 'http_status': pdf.status, 'content_type': pdf.headers.get('content-type'),
                                                 'size_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                                                 'embedded_text': extracted, 'extraction_engine': 'PyMuPDF'})
            return {'target_sku': target, 'url': safe_url(page.url), 'json_endpoints': len(pdp_json),
                    'energyguide_link_count': len(documents), 'energyguide_pdf_valid': True}

        check('pdp_identity_and_documents', pdp)

        def epa():
            dataset = 'p5st-her9'  # observed in official ENERGY STAR catalog, initial hosted artifact
            base = 'https://data.energystar.gov'
            metadata_response = context.request.get(f'{base}/api/views/{dataset}.json', timeout=30000)
            assert metadata_response.status == 200, 'EPA dataset metadata unavailable'
            metadata = metadata_response.json()
            save('fixtures/epa-metadata.json', metadata)
            columns = [{'field': c.get('fieldName'), 'name': c.get('name'), 'type': c.get('dataTypeName')}
                       for c in metadata.get('columns', []) if not c.get('fieldName', '').startswith(':')]
            sample_response = context.request.get(f'{base}/resource/{dataset}.json?$limit=3', timeout=30000)
            assert sample_response.status == 200, 'EPA dataset sample unavailable'
            sample = sample_response.json()
            assert isinstance(sample, list) and sample, 'EPA sample empty'
            save('fixtures/epa-sample.json', sample)
            save('epa-observation.json', {'dataset_id': dataset, 'name': metadata.get('name'),
                                          'rows_updated_at': metadata.get('rowsUpdatedAt'), 'columns': columns,
                                          'sample_rows': len(sample), 'certification_matching': 'NOT_EVALUATED'})
            return {'dataset_id': dataset, 'column_count': len(columns), 'sample_rows': len(sample)}

        check('epa_refrigerator_dataset_contract', epa)
        browser.close()

    report['status'] = 'FAIL' if any(x['status'] == 'FAIL' for x in report['checks']) else 'PASS'
    save('recon.json', report)
    print('Evidence: runtime/source-recon/recon.json', flush=True)
    return int(report['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())

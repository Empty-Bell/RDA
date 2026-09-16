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
            elif 'samsung.com' in url and ('api' in url.lower() or 'bridge_data' in url.lower()):
                try:
                    if 'json' not in response.headers.get('content-type', ''):
                        return
                    data = response.json()
                    paths = profile(sanitize(data))
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
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1500)
                button = page.get_by_role('button', name=re.compile(r'view more|load more|show more', re.I))
                if button.count() and button.first.is_visible():
                    button.first.click(timeout=10000)
                else:
                    link = page.get_by_text(re.compile(r'^view more$', re.I))
                    if link.count() and link.first.is_visible():
                        link.first.click(timeout=10000)
                    else:
                        break
                page.wait_for_timeout(3500)
            exact = {v['modelCode'] for item in all_products.values()
                     for v in [item] + item.get('groupedProductList', [])}
            rendered = page.locator('[data-modelcode]').evaluate_all('(els) => els.map(e => ({tag:e.tagName, cls:e.className, sku:e.getAttribute("data-modelcode")}))')
            save('population-observation.json', {'rounds': rounds, 'groups': len(all_products),
                                                'exact_skus': sorted(exact), 'rendered_candidates': rendered[:200]})
            assert len(all_products) == total, f'Pagination incomplete: {len(all_products)}/{total} groups'
            return {'groups': len(all_products), 'exact_skus': len(exact), 'rounds': rounds,
                    'rendered_count_gate': 'NOT_EVALUATED'}

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
            documents = [x for x in links if re.search(r'energy.?guide', x['text'] or '', re.I)]
            bridge_snippets = re.findall(r'.{0,100}bridge_data.{0,150}', html, re.I)
            save('pdp-observation.json', {'target_sku': target, 'source_url': url, 'final_url': safe_url(page.url),
                                         'http_status': response.status if response else None,
                                         'rendered_target_present': target.lower() in text.lower(),
                                         'energyguide_links': documents, 'bridge_snippets': bridge_snippets[:8],
                                         'json_endpoints': pdp_json})
            assert response and response.status < 400, 'PDP HTTP access failed'
            assert target.lower() in text.lower(), 'Exact SKU not supported by rendered PDP text'
            return {'target_sku': target, 'url': safe_url(page.url), 'json_endpoints': len(pdp_json),
                    'energyguide_link_count': len(documents)}

        check('pdp_identity_and_documents', pdp)
        browser.close()

    report['status'] = 'FAIL' if any(x['status'] == 'FAIL' for x in report['checks']) else 'PASS'
    save('recon.json', report)
    print('Evidence: runtime/source-recon/recon.json', flush=True)
    return int(report['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())

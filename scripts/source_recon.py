"""Bounded product-family source reconnaissance; no compliance rules."""
import argparse
import copy
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs, urlencode

from runner_probe import safe_url, sanitize
from source_contract import pf_page, pf_population, pdp_facts, project_bridge, project_computer_specs, computer_selection, epa_contract, energyguide_ocr_reason
from browser_runtime import desktop_context

OUT = Path('runtime/source-recon')
FAMILIES = {
    'refrigerator': {'plp': 'https://www.samsung.com/us/home-appliances/refrigerators/all-refrigerators/',
                     'dataset': 'p5st-her9', 'dataset_name': 'ENERGY STAR Certified Residential Refrigerators'},
    'dishwasher': {'plp': 'https://www.samsung.com/us/dishwashers/all-dishwashers/',
                   'dataset': 'q8py-6w3f', 'dataset_name': 'ENERGY STAR Certified Residential Dishwashers'},
    'washer': {'plp': 'https://www.samsung.com/us/laundry/washers/',
               'dataset': 'bghd-e2wd', 'dataset_name': 'ENERGY STAR Certified Residential Clothes Washers'},
    'tv': {'plp': 'https://www.samsung.com/us/televisions-home-theater/tvs/all-tvs/',
           'dataset': 'pd96-rr3d', 'dataset_name': 'ENERGY STAR Certified Televisions'},
    'range': {'plp': 'https://www.samsung.com/us/cooking-appliances/ranges/',
              'dataset': 'm6gi-ng33', 'dataset_name': 'ENERGY STAR Certified Residential Electric Cooking Products',
              'recon_domain': 'EPA_ONLY'},
    'cooktop': {'plp': 'https://www.samsung.com/us/cooking-appliances/cooktops/',
                'dataset': 'm6gi-ng33', 'dataset_name': 'ENERGY STAR Certified Residential Electric Cooking Products',
                'recon_domain': 'EPA_ONLY'},
    'dryer': {'plp': 'https://www.samsung.com/us/laundry/dryers/',
              'dataset': 't9u7-4d2j', 'dataset_name': 'ENERGY STAR Certified Residential Clothes Dryers',
              'recon_domain': 'EPA_ONLY'},
    'hood': {'plp': 'https://www.samsung.com/us/cooking-appliances/range-hoods/',
             'dataset': '8dv7-nngq', 'dataset_name': 'ENERGY STAR Certified Ventilating Fans',
             'recon_domain': 'EPA_ONLY'},
    'monitor': {'plp': 'https://www.samsung.com/us/monitors/all-monitors/',
                'dataset': 'qbg3-d468', 'dataset_name': 'ENERGY STAR Certified Displays',
                'recon_domain': 'EPA_ONLY'},
    'computer': {'plp': 'https://www.samsung.com/us/computers/galaxy-book/',
                 'dataset': 'rxdj-2c88', 'dataset_name': 'ENERGY STAR Certified Computers V9.0',
                 'recon_domain': 'EPA_ONLY'},
    'chromebook': {'plp': 'https://www.samsung.com/us/computers/chromebook/',
                   'dataset': 'rxdj-2c88', 'dataset_name': 'ENERGY STAR Certified Computers V9.0',
                   'recon_domain': 'EPA_ONLY'},
    'tablet': {'plp': 'https://www.samsung.com/us/tablets/all-tablets/',
               'dataset': 'rxdj-2c88', 'dataset_name': 'ENERGY STAR Certified Computers V9.0',
               'recon_domain': 'EPA_ONLY'},
}
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
    global OUT
    args = argparse.ArgumentParser()
    args.add_argument('--family', choices=FAMILIES, default='refrigerator')
    family = args.parse_args().family
    config = FAMILIES[family]
    OUT = Path('runtime/source-recon') / family
    from playwright.sync_api import sync_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'captured_at': datetime.now(timezone.utc).isoformat(),
              'run_id': os.getenv('GITHUB_RUN_ID'), 'attempt': os.getenv('GITHUB_RUN_ATTEMPT'),
              'git_sha': os.getenv('GITHUB_SHA'), 'scope': f'{family} source contracts only',
              'status': 'RUNNING', 'phase_gate': 'NOT_EVALUATED', 'observations': [], 'checks': []}
    captured_pf = []
    pdp_json = []
    computer_spec_endpoints = []
    computer_group_ids = []

    def check(name, fn):
        try:
            report['checks'].append({'name': name, 'status': 'PASS', 'details': fn()})
        except Exception as exc:
            report['checks'].append({'name': name, 'status': 'FAIL', 'error': str(exc).splitlines()[0][:250]})
        save('recon.json', report)
        print(f"{name}: {report['checks'][-1]['status']}", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context, identity = desktop_context(browser)
        report['browser_identity'] = identity
        page = context.new_page()
        assert page.evaluate('navigator.userAgent') == identity['user_agent']

        def observe(response):
            url = response.url
            if family in ('computer', 'chromebook', 'tablet') and response.request.resource_type in ('xhr', 'fetch'):
                parsed_url = urlsplit(url)
                if parsed_url.path.endswith('/ecom-data'):
                    computer_group_ids.extend(parse_qs(parsed_url.query).get('group_id', []))
                if parsed_url.hostname == 'www.samsung.com' and not re.search(r'chat|analytics|license|account|auth', parsed_url.path, re.I):
                    endpoint = {'path': parsed_url.path, 'status': response.status}
                    if parsed_url.path.endswith('/bridge-data'):
                        endpoint['data_type'] = parse_qs(parsed_url.query).get('data_type', [])
                        try:
                            payload = response.json()
                            endpoint['sections'] = list(payload) if isinstance(payload, dict) else type(payload).__name__
                        except Exception:
                            endpoint['sections'] = 'NON_JSON'
                    computer_spec_endpoints.append(endpoint)
            if 'pf_search' in url:
                try:
                    data = response.json()
                    payload = response.request.post_data_json
                    projected = project_pf(data)
                    name = f'fixtures/pf-{len(captured_pf)}.json'
                    digest = save(name, projected)
                    row = {'url': safe_url(url), 'method': response.request.method,
                           'status': response.status, 'request_body': payload,
                           'request_user_agent': response.request.headers.get('user-agent'),
                           'fixture': name, 'fixture_sha256': digest,
                           'page_count': len(projected['searchResults'])}
                    report['observations'].append(row)
                    captured_pf.append((data, response.request, payload))
                except Exception as exc:
                    report['observations'].append({'url': safe_url(url), 'status': response.status,
                                                   'request_user_agent': response.request.headers.get('user-agent'),
                                                   'error_type': type(exc).__name__})
            elif '/bridge-data?' in url and 'Specs' in parse_qs(urlsplit(url).query).get('data_type', [''])[0].split(','):
                try:
                    if 'json' not in response.headers.get('content-type', ''):
                        return
                    raw_data = response.json()
                    data = project_computer_specs(raw_data) if family in ('computer', 'chromebook', 'tablet') and isinstance(raw_data, list) else project_bridge(raw_data)
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
            url = config['plp']
            for attempt in range(3):
                response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(8000)
                if captured_pf:
                    break
                if attempt < 2:
                    page.wait_for_timeout(3000 * (2 ** attempt))
            assert response and response.status < 400, 'PLP HTTP access failed'
            assert captured_pf, 'pf_search response was not captured'
            assert all(x.get('request_user_agent') == identity['user_agent']
                       for x in report['observations'] if 'fixture' in x), 'pf_search UA differs from desktop context'
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
            # Repeated requests are not additional population pages; require identical
            # projection for a repeated offset, then validate all unique page offsets.
            unique_pages = {}
            for data, _, body in captured_pf:
                offset = int(body['startIndex'])
                projected = project_pf(data)
                if offset in unique_pages and unique_pages[offset] != projected:
                    raise ValueError('Same pagination offset returned different products')
                unique_pages[offset] = projected
            population = pf_population([unique_pages[i] for i in sorted(unique_pages)])
            exact = {v['modelCode'] for item in all_products.values()
                     for v in [item] + item.get('groupedProductList', [])}
            rendered = page.locator('[data-modelcode]').evaluate_all('(els) => els.map(e => ({tag:e.tagName, cls:e.className, sku:e.getAttribute("data-modelcode")}))')
            visible_links = page.locator('a[href*="-sku-"]:visible').evaluate_all('(els) => els.map(e => e.href.toUpperCase())')
            supported_reps = {x['modelCode'] for x in all_products.values()
                              if any(x['modelCode'] in link for link in visible_links)}
            # API responses arrive before their tiles are mounted; wait for the
            # observed per-card name selector, not arbitrary PDP links/navigation.
            page.wait_for_function('(n) => document.querySelectorAll(".pd21-product-card__name").length >= n',
                                   arg=total, timeout=20000)
            tiles = page.locator('.pd21-product-card__name').evaluate_all(
                '(els) => els.map(e => ({sku:e.getAttribute("data-modelcode"),url:e.href}))')
            tile_groups = []
            for tile in tiles:
                matching = {r['family_id'] for r in population['records'] if r['exact_sku'] == tile['sku']}
                assert len(matching) == 1, 'Rendered tile SKU has missing/ambiguous population provenance'
                tile_groups.append(next(iter(matching)))
            save('population-observation.json', {'rounds': rounds, 'groups': len(all_products),
                                                'exact_skus': sorted(exact), 'rendered_candidates': rendered[:200],
                                                'rendered_representative_link_count': len(supported_reps),
                                                'rendered_tiles': tiles, 'rendered_tile_groups': tile_groups})
            assert len(all_products) == total, f'Pagination incomplete: {len(all_products)}/{total} groups'
            assert len(tiles) == len(set(tile_groups)) == total, 'Rendered tile/API group counts do not reconcile'
            return {'groups': len(all_products), 'exact_skus': len(exact), 'rounds': rounds,
                    'rendered_representative_link_count': len(supported_reps),
                    'rendered_tile_count': len(tiles), 'strict_tile_count_gate': 'PASS'}

        check('pagination_observation', pagination)

        def pdp(sample_product=None):
            if sample_product is not None:
                product = sample_product
                sampling_source = 'current pf_search; additional source-backed diagnostic sample'
            elif captured_pf:
                product = captured_pf[0][0]['searchResults'][0]
                sampling_source = 'current pf_search response'
            else:
                # Historical fixture is a diagnostic sample only, never current population.
                fixture = Path('tests/fixtures') / family / 'pf-page-0.json'
                assert fixture.exists(), 'No live population or prior family fixture; cannot guess PDP'
                product = json.loads(fixture.read_text(encoding='utf-8'))['searchResults'][0]
                sampling_source = 'previous hosted fixture; independent source diagnosis, not population'
            target = product['modelCode']
            url = urljoin('https://www.samsung.com', product['pdpURL'])
            if family in ('computer', 'chromebook', 'tablet'):
                computer_group_ids.clear()
            response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(10000)
            if family in ('computer', 'chromebook', 'tablet'):
                # Current selected controls plus exact backend Specs corroborate SKU.
                try:
                    page.locator('[data-modelcode][aria-checked="true"]').first.wait_for(state='visible', timeout=30000)
                finally:
                    save('computer-spec-endpoints.json', computer_spec_endpoints)
                    purchase_control = page.get_by_role('button', name=re.compile(r'^Continue')).first
                    selection = {
                        'target_sku': target, 'final_url': safe_url(page.url),
                        'rendered_target_present': target.lower() in page.locator('body').inner_text().lower(),
                        'selected_controls': page.locator('[data-modelcode][aria-checked="true"]').evaluate_all(
                            '(els) => els.map(e => ({sku:e.getAttribute("data-modelcode"),label:e.getAttribute("aria-label")}))'),
                        'continue_sku': purchase_control.get_attribute('data-modelcode') if purchase_control.count() else None,
                        'continue_visible': purchase_control.is_visible() if purchase_control.count() else False}
                    save('computer-configurator-observation.json', selection)
                computer_selection(selection, target)
                assert len(set(computer_group_ids)) == 1, 'Missing/ambiguous current ecom-data group provenance'
                spec_url = 'https://www.samsung.com/us/gapi/v1/bridge/cacheable/bridge-data?' + urlencode({
                    'data_type': 'Specs', 'store_type': 'B2C', 'group_id': computer_group_ids[0],
                    'modelCode': target, 'version': 'v2'})
                spec_response = context.request.get(spec_url, timeout=30000)
                assert spec_response.status == 200, 'Computer Specs request failed'
                projected = project_computer_specs(spec_response.json())
                index = len(pdp_json)
                fixture_name = f'fixtures/pdp-{index}.json'
                digest = save(fixture_name, projected)
                pdp_json.append({'url': safe_url(spec_url), 'method': 'GET', 'status': spec_response.status,
                                 'fixture': fixture_name, 'fixture_sha256': digest,
                                 'sampling_source': 'observed Specs pattern; current ecom-data group and selected SKU'})
            text = page.locator('body').inner_text()
            html = page.content()
            links = page.locator('a[href]').evaluate_all('(els) => els.map(e => ({text:e.textContent,url:e.href}))')
            documents = [x for x in links if re.search(r'energy\s*guide', x['text'] or '', re.I)]
            bridge_snippets = re.findall(r'.{0,100}bridge_data.{0,150}', html, re.I)
            save('pdp-observation.json', {'target_sku': target, 'source_url': url, 'final_url': safe_url(page.url),
                                         'sampling_source': sampling_source,
                                         'http_status': response.status if response else None,
                                         'rendered_target_present': target.lower() in text.lower(),
                                         'energyguide_links': documents, 'bridge_snippets': bridge_snippets[:8],
                                         'json_endpoints': pdp_json})
            if family in ('computer', 'chromebook', 'tablet'):
                save('computer-spec-endpoints.json', computer_spec_endpoints)
            assert response and response.status < 400, 'PDP HTTP access failed'
            if family not in ('computer', 'chromebook', 'tablet'):
                assert target.lower() in text.lower(), 'Exact SKU not supported by rendered PDP text'
            assert pdp_json, 'Specs/Support bridge-data endpoint was not observed'
            source = json.loads((OUT / pdp_json[0]['fixture']).read_text(encoding='utf-8'))
            facts = pdp_facts(source, target, family='computer' if family == 'chromebook' else family)
            save('pdp-facts.json', facts)
            if config.get('recon_domain') == 'EPA_ONLY':
                return {'target_sku': target, 'url': safe_url(page.url), 'json_endpoints': len(pdp_json),
                        'energyguide_metadata_count': None if facts['document_collection_status'] == 'NOT_EVALUATED' else len(facts['energyguide_documents']),
                        'document_collection_status': facts['document_collection_status'],
                        'energyguide_probe': 'OUT_OF_RECON_SCOPE', 'certification_matching': 'NOT_EVALUATED'}
            assert facts['energyguide_documents'], 'No EnergyGuide metadata in target Support record'
            document = facts['energyguide_documents'][0]
            pdf = context.request.get(document['url'], timeout=30000)
            raw = pdf.body()
            assert pdf.status == 200 and raw.startswith(b'%PDF-'), 'EnergyGuide response is not a valid PDF'
            import pymupdf
            parsed = pymupdf.open(stream=raw, filetype='pdf')
            extracted = '\n'.join(p.get_text() for p in parsed)
            (OUT / 'energyguide-original.pdf').write_bytes(raw)
            ocr_texts = []
            fallback_reason = None
            engine_name = 'PyMuPDF'
            if energyguide_ocr_reason(extracted):
                import cv2
                from rapidocr import RapidOCR
                cv2.setNumThreads(1)
                fallback_reason = energyguide_ocr_reason(extracted)
                parsed[0].get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(OUT / 'energyguide-ocr-2x.png')
                engine = RapidOCR(params={'EngineConfig.onnxruntime.intra_op_num_threads': 1,
                                          'EngineConfig.onnxruntime.inter_op_num_threads': 1})
                result = engine(str(OUT / 'energyguide-ocr-2x.png'))
                ocr_texts = list(result.txts or [])
                assert ocr_texts, 'EnergyGuide image-only OCR failed'
                engine_name = 'RapidOCR'
            save('energyguide-observation.json', {'requested_url': document['url'], 'final_url': safe_url(pdf.url),
                                                 'http_status': pdf.status, 'content_type': pdf.headers.get('content-type'),
                                                 'size_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                                                 'embedded_text': extracted, 'extraction_engine': engine_name,
                                                 'fallback_reason': fallback_reason, 'ocr_raw_texts': ocr_texts,
                                                 'ocr_scale': 2 if ocr_texts else None,
                                                 'field_parser_contract': 'NOT_EVALUATED'})
            return {'target_sku': target, 'url': safe_url(page.url), 'json_endpoints': len(pdp_json),
                    'energyguide_link_count': len(documents), 'energyguide_pdf_valid': True}

        check('pdp_identity_and_documents', pdp)

        if family in {'washer', 'dryer'}:
            # Observed standalone listing paths provide a second diagnostic sample;
            # this is not certification routing or a model-prefix classification rule.
            candidates = [x for data, _, _ in captured_pf for x in data['searchResults']
                          if f'/us/laundry/{"washers" if family == "washer" else "dryers"}/' in x.get('pdpURL', '')]
            base_out = OUT
            OUT = base_out / 'standalone'
            pdp_json.clear()  # never select the earlier combo's bridge record
            def standalone():
                assert candidates, 'No source-backed standalone-path sample'
                return pdp(candidates[0])
            check(f'standalone_{family}_pdp_and_documents', standalone)
            OUT = base_out

        if family == 'cooktop':
            candidates = [x for data, _, _ in captured_pf for x in data['searchResults']
                          if 'electric-cooktop' in x.get('pdpURL', '')]
            base_out = OUT
            OUT = base_out / 'electric'
            pdp_json.clear()
            def electric():
                assert candidates, 'No source-backed electric-path sample'
                return pdp(candidates[0])
            check('electric_cooktop_pdp_contract', electric)
            OUT = base_out

        def epa():
            dataset = config['dataset']  # discovered from official catalog; live identity checked below
            base = 'https://data.energystar.gov'
            metadata_response = context.request.get(f'{base}/api/views/{dataset}.json', timeout=30000)
            assert metadata_response.status == 200, 'EPA dataset metadata unavailable'
            metadata = metadata_response.json()
            assert metadata.get('name') == config['dataset_name'], 'EPA certified dataset name drifted'
            # Public data schema only; omit publisher/contact/account metadata.
            projected_metadata = {k: metadata.get(k) for k in ('id', 'name', 'rowsUpdatedAt')}
            projected_metadata['columns'] = [{k: c.get(k) for k in ('fieldName', 'name', 'dataTypeName')}
                                             for c in metadata.get('columns', [])
                                             if not c.get('fieldName', '').startswith(':')]
            save('fixtures/epa-metadata.json', projected_metadata)
            columns = [{'field': c.get('fieldName'), 'name': c.get('name'), 'type': c.get('dataTypeName')}
                       for c in metadata.get('columns', []) if not c.get('fieldName', '').startswith(':')]
            sample_response = context.request.get(f'{base}/resource/{dataset}.json?$limit=3', timeout=30000)
            assert sample_response.status == 200, 'EPA dataset sample unavailable'
            sample = sample_response.json()
            assert isinstance(sample, list) and sample, 'EPA sample empty'
            save('fixtures/epa-sample.json', sample)
            epa_contract(metadata, sample, dataset=dataset)
            save('epa-observation.json', {'dataset_id': dataset, 'name': metadata.get('name'),
                                          'rows_updated_at': metadata.get('rowsUpdatedAt'), 'columns': columns,
                                          'sample_rows': len(sample), 'certification_matching': 'NOT_EVALUATED'})
            return {'dataset_id': dataset, 'column_count': len(columns), 'sample_rows': len(sample)}

        check(f'epa_{family}_dataset_contract', epa)
        browser.close()

    report['status'] = 'FAIL' if any(x['status'] == 'FAIL' for x in report['checks']) else 'PASS'
    save('recon.json', report)
    print('Evidence: runtime/source-recon/recon.json', flush=True)
    return int(report['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())

"""Phase 0 diagnostic only: no product population or compliance verdict."""
import hashlib
import json
import os
import platform
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

OUT = Path('runtime')
SENSITIVE = re.compile(r'cookie|authorization|token|secret|password|email|session|feedbackParam|metricsParam|userId|visitorId', re.I)


def safe_url(url):
    p = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not SENSITIVE.search(k)]
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(query), ''))


def sanitize(value):
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items() if not SENSITIVE.search(k)}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value


def valid_pdf(data):
    return bool(data) and data.startswith(b'%PDF-')


def write_json(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    report = {
        'phase': 0, 'scope': 'runtime and refrigerator reconnaissance sample',
        'automatic_final_legal_conclusion': False,
        'started_at': datetime.now(timezone.utc).isoformat(),
        'github_run_id': os.getenv('GITHUB_RUN_ID'),
        'github_run_attempt': os.getenv('GITHUB_RUN_ATTEMPT'),
        'git_sha': os.getenv('GITHUB_SHA'),
        'runner_image': os.getenv('ImageOS'), 'runner_image_version': os.getenv('ImageVersion'),
        'python': platform.python_version(), 'platform': platform.platform(), 'checks': [],
        'full_phase_gate': 'NOT_EVALUATED',
    }

    def check(name, fn):
        started = time.monotonic()
        try:
            details = fn()
            row = {'name': name, 'status': 'PASS', 'details': details}
        except Exception as exc:
            # Do not serialize request headers or exception URLs/query credentials.
            row = {'name': name, 'status': 'FAIL', 'error_type': type(exc).__name__,
                   'reason': str(exc).splitlines()[0][:240]}
        row['elapsed_seconds'] = round(time.monotonic() - started, 2)
        report['checks'].append(row)
        write_json('probe.json', report)
        print(f"{name}: {row['status']}", flush=True)

    def disk():
        free = shutil.disk_usage(OUT).free
        assert free >= 3 * 1024**3, 'Less than 3 GiB free disk'
        return {'free_bytes': free}

    def pdf_and_ocr():
        import cv2
        import pymupdf
        from rapidocr import RapidOCR
        cv2.setNumThreads(1)
        doc = pymupdf.open()
        page = doc.new_page(width=612, height=300)
        page.insert_text((35, 80), 'EnergyGuide TEST MODEL RF28B1234', fontsize=22)
        page.insert_text((35, 125), 'Annual energy use 685 kWh', fontsize=22)
        raw = doc.tobytes()
        assert valid_pdf(raw)
        (OUT / 'synthetic-embedded.pdf').write_bytes(raw)
        assert '685' in page.get_text()
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        image_doc = pymupdf.open()
        image_page = image_doc.new_page(width=612, height=300)
        image_page.insert_image(image_page.rect, stream=pix.tobytes('png'))
        assert not image_page.get_text().strip()
        image_doc.save(OUT / 'synthetic-image-only.pdf')
        image_page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(OUT / 'synthetic-ocr.png')
        engine = RapidOCR(params={'EngineConfig.onnxruntime.intra_op_num_threads': 1,
                                  'EngineConfig.onnxruntime.inter_op_num_threads': 1})
        result = engine(str(OUT / 'synthetic-ocr.png'))
        texts = list(result.txts or [])
        assert any('685' in text for text in texts), 'OCR did not recognize synthetic 685'
        write_json('synthetic-ocr.json', {'raw_texts': texts, 'engine': 'RapidOCR', 'scale': 2})
        return {'embedded_text': True, 'image_only_fallback': True, 'ocr_texts': texts}

    def browser_sources():
        from playwright.sync_api import sync_playwright
        from browser_runtime import desktop_context
        observations = []
        captures = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context, identity = desktop_context(browser)
            report['browser_identity'] = identity
            page = context.new_page()
            assert page.evaluate('navigator.userAgent') == identity['user_agent']

            def observe(response):
                url = response.url
                if not re.search(r'pf_search|bridge_data', url, re.I):
                    return
                row = {'url': safe_url(url), 'method': response.request.method,
                       'status': response.status}
                try:
                    payload = response.json()
                    name = f'fixtures/samsung-{len(captures)}.json'
                    if len(captures) < 8:
                        row['fixture'] = name
                        row['fixture_sha256'] = write_json(name, sanitize(payload))
                        captures.append(row)
                except Exception:
                    row['json_status'] = 'UNAVAILABLE'
                observations.append(row)

            page.on('response', observe)
            url = 'https://www.samsung.com/us/home-appliances/refrigerators/all-refrigerators/'
            response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(10000)
            status = response.status if response else None
            links = page.locator('a[href]').evaluate_all('(els) => els.map(e => e.href)')
            pdps = list(dict.fromkeys(u for u in links if '/us/' in u and re.search(r'-[a-z0-9]+/$', u)
                                    and '/refrigerators/' in u and 'all-refrigerators' not in u))
            write_json('samsung-network.json', {'observations': observations, 'plp_status': status,
                                              'final_url': safe_url(page.url), 'pdp_candidates': pdps[:5]})
            assert status and status < 400, f'Samsung PLP HTTP {status}'
            assert any('pf_search' in row['url'] and row['status'] == 200 for row in observations), \
                'Current pf_search was not observed; source contract remains unverified'
            if pdps:
                page.goto(pdps[0], wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(10000)
                write_json('samsung-network.json', {'observations': observations, 'plp_status': status,
                                                  'pdp_sample_url': safe_url(page.url)})
            browser.close()
        return {'observed_endpoints': len(observations), 'pdp_sample_attempted': bool(pdps)}

    def epa_catalog():
        url = 'https://api.us.socrata.com/api/catalog/v1?search_context=data.energystar.gov&q=refrigerators&limit=5'
        with urlopen(Request(url, headers={'User-Agent': 'RDA-Phase0-Recon/0.1'}), timeout=30) as response:
            payload = json.load(response)
        results = payload.get('results', [])
        assert results, 'No official catalog results; dataset contract remains unverified'
        digest = write_json('fixtures/epa-catalog.json', sanitize(payload))
        return {'url': safe_url(url), 'result_count': len(results), 'fixture_sha256': digest,
                'certification_lookup': 'NOT_EVALUATED'}

    check('disk_budget', disk)
    check('embedded_pdf_and_image_only_ocr', pdf_and_ocr)
    check('headless_chromium_and_samsung', browser_sources)
    check('epa_catalog_access', epa_catalog)
    report['completed_at'] = datetime.now(timezone.utc).isoformat()
    report['probe_status'] = 'FAIL' if any(c['status'] == 'FAIL' for c in report['checks']) else 'PASS'
    write_json('probe.json', report)
    summary = os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as f:
            f.write('## Phase 0 probe (not full phase acceptance)\n\n')
            for row in report['checks']:
                f.write(f"- {row['name']}: {row['status']} ({row['elapsed_seconds']}s)\n")
            f.write('\nNo compliance verdict. Full Phase 0 gate remains NOT_EVALUATED.\n')
    return int(report['probe_status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())

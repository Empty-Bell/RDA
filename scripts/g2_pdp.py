"""Bounded per-SKU PDP identity collection; no compliance interpretation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, parse_qs
from source_contract import pdp_facts, project_bridge
from browser_runtime import desktop_context
from claim_recon import DOM_SNAPSHOT
from runner_probe import safe_url


def select_sample(products, existing_sku, limit=5):
    if type(limit) is not int or not 1<=limit<=10:raise ValueError('Pilot bound must be 1..10')
    by_sku={p['exact_sku']:p for p in products}
    if len(by_sku)!=len(products) or existing_sku not in by_sku:raise ValueError('Invalid sample population')
    selected=[existing_sku]
    for role in ('REPRESENTATIVE','VARIANT'):
        candidates=sorted(p['exact_sku'] for p in products if any(l['sku_role']==role for l in p['listings']))
        for sku in candidates:
            if len(selected)==limit:break
            if sku not in selected:selected.append(sku);break
    for sku in sorted(by_sku):
        if len(selected)==limit:break
        if sku not in selected:selected.append(sku)
    return [by_sku[sku] for sku in selected]


def verify_identity(sku, final_url, snapshot, bridge):
    parts=urlsplit(final_url)
    # Samsung source URL spelling only; the actual SKU key/model is never altered.
    slug=re.escape(sku.lower().replace('/','-'))
    if parts.scheme!='https' or parts.hostname!='www.samsung.com' or '/us/' not in parts.path or not re.search(r'-sku-'+slug+r'/?$',parts.path.lower()):
        raise ValueError('Final PDP URL refers to another SKU/surface')
    if snapshot.get('jsonld_parse_errors'):raise ValueError('Product identity JSON-LD parse failed')
    declarations=snapshot.get('product_jsonld')
    if not isinstance(declarations,list) or not declarations:raise ValueError('Current product SKU declaration unobserved')
    for declared in declarations:
        identifiers=[declared[k] for k in ('sku','mpn') if declared.get(k)]
        if not identifiers or any(v!=sku for v in identifiers):raise ValueError('Current selected product declaration disagrees with exact SKU')
    return pdp_facts(bridge,sku,family='refrigerator')


def coverage(products, results):
    population={p['exact_sku'] for p in products}
    if len(population)!=len(products):raise ValueError('Duplicate product identity')
    seen={r['exact_sku'] for r in results}
    if len(seen)!=len(results) or not seen<=population:raise ValueError('Coverage has duplicate/unknown SKU')
    if any(r['status'] not in ('VERIFIED_EXACT_IDENTITY','FAILED') for r in results):raise ValueError('Unknown PDP collection status')
    entries={r['exact_sku']:r['status'] for r in results}
    rows=[{'exact_sku':sku,'pdp_collection_status':entries.get(sku,'NOT_ATTEMPTED')} for sku in sorted(population)]
    counts={status:sum(r['pdp_collection_status']==status for r in rows)
            for status in ('VERIFIED_EXACT_IDENTITY','FAILED','NOT_ATTEMPTED')}
    return {'scope':'PDP source identity only; not assessment/domain coverage',
            'population_count':len(population),'attempted_count':len(results),'counts':counts,'rows':rows}


def collect_samples(products, output):
    from playwright.sync_api import sync_playwright
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context,identity=desktop_context(browser)
        for number,product in enumerate(products):
            sku=product['exact_sku'];folder=output/str(number);folder.mkdir()
            result={'exact_sku':sku,'status':'FAILED','requested_url':product['listings'][0]['pdp_url'],
                    'browser_identity':identity,'responses':[],'observations':[]}
            page=context.new_page()
            def receive(response):
                query=parse_qs(urlsplit(response.url).query)
                if '/bridge-data?' not in response.url or 'Specs' not in query.get('data_type',[''])[0].split(','):return
                entry={'url':safe_url(response.url),'status':response.status,
                       'captured_at':datetime.now(timezone.utc).isoformat()}
                result['responses'].append(entry)
                try:
                    if len(result['responses'])>8:raise ValueError('PDP response bound exceeded')
                    if response.status!=200 or 'json' not in response.headers.get('content-type','').lower():raise ValueError('PDP bridge response inaccessible/not JSON')
                    projected=project_bridge(response.json())
                    raw=(json.dumps(projected,sort_keys=True,indent=2)+'\n').encode()
                    path=folder/('bridge-'+str(len(result['responses']))+'.json');path.write_bytes(raw)
                    entry.update(path=str(path),sha256=hashlib.sha256(raw).hexdigest())
                except Exception as error:entry['error_class']=type(error).__name__
            page.on('response',receive)
            try:
                response=page.goto(result['requested_url'],wait_until='domcontentloaded',timeout=60000)
                page.wait_for_timeout(10000)
                result.update(final_url=safe_url(page.url),http_status=response.status if response else None)
                snapshot=page.evaluate(DOM_SNAPSHOT)
                # A page can still supply exact PDP identity and logo evidence when its
                # interactive Specs tab is unavailable.  Preserve that evidence and mark
                # only the spec-table point UNKNOWN; never turn an interaction timeout
                # into an absence finding or abort the rest of the bounded pilot.
                try:
                    specs=page.get_by_role('button',name=re.compile(r'^Specs$',re.I))
                    if specs.count()!=1:raise ValueError('PDP Specs navigation is missing or ambiguous')
                    try:
                        specs.click(timeout=5000)
                    except Exception as click_error:
                        # Samsung's fixed page chrome can cover the otherwise visible
                        # tab on a hosted headless viewport.  Retry the same unique
                        # control once; surface contents are still verified below.
                        if type(click_error).__name__!='TimeoutError':raise
                        specs.click(timeout=3000,force=True)
                    page.wait_for_timeout(1000)
                    spec_root=page.locator('#specs')
                    if spec_root.count()!=1:raise ValueError('PDP Specs surface did not mount')
                    # Samsung currently mounts the full table when its Specs tab opens.
                    # Do not click an optional toggle without first observing that the rows are absent.
                    if spec_root.locator('[class*="Specs_subSpecItem__"]').count()==0:
                        expand=spec_root.get_by_role('button',name=re.compile(r'^See All Specs$',re.I))
                        if expand.count()!=1:raise ValueError('PDP Specs table is unavailable or ambiguous')
                        expand.click(timeout=10000)
                        page.wait_for_timeout(1000)
                    snapshot=page.evaluate(DOM_SNAPSHOT)
                    result['spec_surface_interaction']='SPECS_NAVIGATION_SUCCESS'
                except Exception as spec_error:
                    result['spec_surface_interaction']='SPECS_NAVIGATION_UNAVAILABLE'
                    result['spec_surface_error_class']=type(spec_error).__name__
                raw=(json.dumps(snapshot,sort_keys=True,indent=2)+'\n').encode();path=folder/'snapshot.json';path.write_bytes(raw)
                result['observations'].append({'url':safe_url(page.url),'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),
                                               'captured_at':datetime.now(timezone.utc).isoformat()})
                if not response or response.status!=200:raise ValueError('PDP HTTP failure')
                candidates=[]
                for entry in result['responses']:
                    if 'path' not in entry:continue
                    try:
                        facts=verify_identity(sku,page.url,snapshot,json.loads(Path(entry['path']).read_bytes()))
                    except ValueError:continue
                    candidates.append((entry,facts))
                if not candidates:raise ValueError('No exact current URL/JSON-LD/Specs/Support identity evidence')
                if len({entry['sha256'] for entry,_ in candidates})!=1:raise ValueError('Same SKU bridge changed during collection')
                entry,facts=candidates[0]
                result.update(status='VERIFIED_EXACT_IDENTITY',bridge=entry,pdp_facts_raw=facts,
                              identity_contract='FINAL_URL_AND_CURRENT_JSONLD_AND_EXACT_SPECS_SUPPORT')
            except Exception as error:result['error_class']=type(error).__name__
            finally:
                page.close()
                (folder/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
            results.append(result)
        context.close();browser.close()
    return results

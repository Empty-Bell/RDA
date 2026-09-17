"""Bounded observational smoke: whole listing, one PDP/PDF, brand EPA snapshot."""
from datetime import datetime, timezone
from dataclasses import fields
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from regaudit.config import load_configuration
from regaudit.contracts import dumps, validate_bundle, verify_evidence_files
from regaudit.facts import TYPES
from regaudit.report import summarize_bundle
from g2_population import observation, population_records
from source_contract import pdp_facts
from source_recon import FAMILIES


def main():
    run_id=uuid.uuid4().hex
    out=ROOT/'runtime/g2'/run_id;out.mkdir(parents=True,exist_ok=False)
    started=datetime.now(timezone.utc).isoformat()
    checkpoint={'status':'FAILED','scope':'G2 observational pilot; no assessment',
                'phase_gate':'NOT_EVALUATED','run_id':run_id,'github_run_id':os.getenv('GITHUB_RUN_ID'),
                'github_run_attempt':os.getenv('GITHUB_RUN_ATTEMPT'),'git_sha':os.getenv('GITHUB_SHA'),
                'started_at':started,'rule_evaluation':'NOT_EVALUATED'}
    try:
        for script in ('source_recon.py','epa_recon.py'):
            subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--family','refrigerator'],cwd=ROOT,check=True,timeout=900)
        source=ROOT/'runtime/source-recon/refrigerator';epa=ROOT/'runtime/epa-query/p5st-her9'
        recon=json.loads((source/'recon.json').read_bytes());epa_recon=json.loads((epa/'recon.json').read_bytes())
        for report in (recon,epa_recon):
            if report['status']!='PASS' or report['run_id']!=os.getenv('GITHUB_RUN_ID') or report['git_sha']!=os.getenv('GITHUB_SHA'):
                raise ValueError('Collector failure or mixed execution provenance')
        pages={};page_sources={}
        for entry in recon['observations']:
            if 'request_body' not in entry:continue
            offset=int(entry['request_body']['startIndex']);raw=(source/entry['fixture']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=entry['fixture_sha256']:raise ValueError('PF hash mismatch')
            if offset in pages and pages[offset]!=raw:raise ValueError('Same offset changed')
            pages[offset]=raw;page_sources[offset]=entry['url']
        ordered=sorted(pages)
        products,parsed=population_records([pages[i] for i in ordered],run_id,FAMILIES['refrigerator']['plp'])
        config,config_hash=load_configuration(ROOT)
        bundle={'manifest':{'schema_version':'draft-1','run_id':run_id,'started_at':started,'completed_at':None,
            'git_sha':os.environ['GITHUB_SHA'],'config_hash':config_hash,'rule_version':None,
            'source_contract_version':config['sources']['contract_version'],'python_version':sys.version.split()[0],
            'playwright_version':__import__('importlib.metadata',fromlist=['version']).version('playwright'),
            'runner':'ubuntu-24.04-x64','overall_execution_status':'PARTIAL','assessment_enabled':False},
            'products':products,'evidence':[],'facts':[],'assessments':[]}
        def evidence(raw,url,sku,kind):
            digest=hashlib.sha256(raw).hexdigest();relative='raw/'+digest+'.bin';path=out/relative
            path.parent.mkdir(exist_ok=True)
            if not path.exists():
                with path.open('xb') as stream:stream.write(raw)
            elif path.read_bytes()!=raw:raise ValueError('Raw hash collision')
            identity='e-'+str(len(bundle['evidence']))
            bundle['evidence'].append({'evidence_id':identity,'run_id':run_id,'product_group':'refrigerator',
                'sku':sku,'source_url':url,'captured_at':started,'sha256':digest,'parser_version':'g2-observation-1',
                'evidence_type':kind,'relative_path':relative})
            return identity,digest
        for offset in ordered:
            members={r['modelCode'] for g in json.loads(pages[offset])['searchResults'] for r in g['groupedProductList']}
            for sku in sorted(members):evidence(pages[offset],page_sources[offset],sku,'projected-public-pf-response')
        pdp=json.loads((source/'pdp-observation.json').read_bytes());sku=pdp['target_sku']
        if sku not in {p['exact_sku'] for p in products}:raise ValueError('Sample outside population')
        bridge=pdp['json_endpoints'][0];raw=(source/bridge['fixture']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=bridge['fixture_sha256']:raise ValueError('Bridge hash mismatch')
        parsed_pdp=pdp_facts(json.loads(raw),sku)
        bridge_id,bridge_hash=evidence(raw,bridge['url'],sku,'projected-public-bridge-response')
        for name in ('pdp-facts.json','public-claim-facts.json','fixtures/public-claim-snapshot.json'):
            evidence((source/name).read_bytes(),pdp['final_url'],sku,'uninterpreted-pdp-observation')
        def fact(kind,values,refs):
            observations={f.name:observation() for f in fields(TYPES[kind])};observations.update(values)
            bundle['facts'].append({'fact_id':'f-'+kind,'run_id':run_id,'product_group':'refrigerator',
                'exact_sku':sku,'kind':kind,'observations':observations,'evidence_ids':refs})
        fact('PDP',{'pdp_model':observation(sku),'pdp_url':observation(pdp['final_url']),
             'source_bridge_hash':observation(bridge_hash)},[bridge_id])
        label=json.loads((source/'energyguide-observation.json').read_bytes());raw=(source/'energyguide-original.pdf').read_bytes()
        if not raw.startswith(b'%PDF-') or hashlib.sha256(raw).hexdigest()!=label['sha256']:raise ValueError('Label bytes mismatch')
        if label['requested_url'] not in {d['url'] for d in parsed_pdp['energyguide_documents']}:raise ValueError('Label outside selected SKU support')
        label_id,label_hash=evidence(raw,label['requested_url'],sku,'original-energyguide-pdf')
        extraction_id,_=evidence((source/'energyguide-observation.json').read_bytes(),label['requested_url'],sku,'extraction-observation')
        for name in ('energyguide-field-candidates.json','energyguide-layout-candidates.json'):
            evidence((source/name).read_bytes(),label['requested_url'],sku,'unselected-label-field-candidates')
        fact('ENERGYGUIDE',{'document_url':observation(label['requested_url']),'document_sha256':observation(label_hash),
             'document_status':observation('SOURCE_PDF_PARSED'),'extraction_engine':observation(label['extraction_engine']),
             'embedded_text':observation(label['embedded_text']),'ocr_raw_text':observation('\n'.join(label['ocr_raw_texts'])),
             'fallback_reason':observation(label['fallback_reason']),'ocr_scale':observation(label['ocr_scale'])},[label_id,extraction_id])
        # Dataset-query context is not evidence of a product certification match.
        for entry in epa_recon['responses']:
            path=epa/(entry['name']+'-response.bin')
            if path.exists():
                raw=path.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=entry['body_sha256']:raise ValueError('EPA response hash mismatch')
                evidence(raw,entry['url'],sku,'epa-dataset-query-context-not-sku-match')
        for domain in ('FTC','EPA'):
            bundle['assessments'].append({'assessment_id':'a-'+domain,'run_id':run_id,'product_group':'refrigerator',
                'exact_sku':sku,'regulatory_domain':domain,'control_id':'PILOT_COLLECTION_SCOPE','rule_id':None,'rule_version':None,
                'assessment_status':'NOT_EVALUATED','severity':None,'issue_code':None,
                'reason':'Rule evaluation disabled; dataset context does not establish certification match',
                'expected':None,'observed':None,'evidence_ids':[bridge_id] if domain=='FTC' else [],'automatic_final_legal_conclusion':False})
        bundle['manifest']['completed_at']=datetime.now(timezone.utc).isoformat()
        validate_bundle(bundle);verify_evidence_files(bundle,out)
        for name,data in [('bundle.json',bundle),('report.json',summarize_bundle(bundle))]:
            with (out/name).open('x',encoding='utf-8',newline='\n') as stream:stream.write(dumps(data))
        checkpoint.update(status='PASS',population_groups=parsed['total_groups'],population_skus=len(products),
            collected_pdp_skus=[sku],collected_label_skus=[sku],epa_brand_scan=epa_recon['brand_scan'],
            sku_certification_matching='NOT_EVALUATED',bundle_sha256=hashlib.sha256((out/'bundle.json').read_bytes()).hexdigest())
    except Exception as error:
        checkpoint['error_class']=type(error).__name__
        print('G2_PILOT_FAILED: '+str(error),file=sys.stderr)
    finally:
        (out/'checkpoint.json').write_text(dumps(checkpoint),encoding='utf-8')
    return 0 if checkpoint['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())

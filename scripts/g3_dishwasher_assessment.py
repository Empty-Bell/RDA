import argparse,json,os,re
from collections import Counter
from pathlib import Path
RANK={"LOW":1,"MEDIUM":2,"HIGH":3}
def load(p): return json.loads(Path(p).read_bytes())

def readiness(energy, numeric, model):
 """Block final verdicts until each source control is complete and bound."""
 sources={"energy_star":energy,"numeric":numeric,"model":model}
 gaps=[]
 fingerprints={name:source.get('source_bundle_fingerprint') for name,source in sources.items()}
 if any(not isinstance(fp,str) or not fp.startswith('sha256:') for fp in fingerprints.values()) or len(set(fingerprints.values()))!=1:
  gaps.append({'code':'CONTROL_SOURCE_BUNDLE_UNBOUND','source_bundle_fingerprints':fingerprints})
 packages={name:source.get('source_package_sha256') for name,source in sources.items() if name in ('numeric','model')}
 if any(not isinstance(digest,str) or len(digest)!=64 for digest in packages.values()) or len(set(packages.values()))!=1:
  gaps.append({'code':'CONTROL_COMPARISON_PACKAGE_DIFFERS','source_package_sha256':packages})
 indices={}
 for name,source in sources.items():
  if source.get('status')!='PASS': gaps.append({'code':'CONTROL_SOURCE_NOT_PASS','control':name})
  records=source.get('rows' if name=='numeric' else 'records',[])
  if not isinstance(records,list) or not records:
   gaps.append({'code':'CONTROL_RECORDS_MISSING','control':name});continue
  index={row.get('exact_sku'):row for row in records if isinstance(row,dict)}
  if len(index)!=len(records) or None in index: gaps.append({'code':'CONTROL_SKU_DUPLICATE_OR_MISSING','control':name})
  indices[name]=index
 if len(indices)!=3 or set(indices['energy_star'])!=set(indices['numeric']) or set(indices['energy_star'])!=set(indices['model']):
  gaps.append({'code':'CONTROL_SKU_COVERAGE_DIFFERS'})
 for sku,row in sorted(indices.get('numeric',{}).items()):
  if row.get('energyguide_annual_energy',{}).get('state')!='VALUE':
   gaps.append({'code':'US_ENERGYGUIDE_ANNUAL_UNRESOLVED','exact_sku':sku})
  if row.get('pdp_vs_energyguide_energy')=='NOT_COMPARABLE' and row.get('pdp_annual_energy',{}).get('state')=='VALUE':
   gaps.append({'code':'PDP_LABEL_NUMERIC_UNRESOLVED','exact_sku':sku})
 for sku,row in sorted(indices.get('model',{}).items()):
  if row.get('pdp_vs_energyguide_model')=='DIFFERENT' and row.get('energyguide_model_pattern_source')!='HUMAN_VISUAL_REVIEW':
   gaps.append({'code':'RAW_OCR_MODEL_MISMATCH_UNREVIEWED','exact_sku':sku})
  if row.get('pdp_vs_energyguide_model')=='DIFFERENT' and row.get('energyguide_model_pattern_source')=='HUMAN_VISUAL_REVIEW':
   identifier=row.get('normalized_pdp_model','')
   patterns=row.get('energyguide_model_patterns_visual_reviewed',[])
   if any(identifier.startswith(re.split(r'[*?]',re.sub(r'[^A-Z0-9*?]','',value.upper()),maxsplit=1)[0]) for value in patterns if isinstance(value,str) and ('*' in value or '?' in value)):
    gaps.append({'code':'MODEL_PATTERN_SUFFIX_POLICY_UNAPPROVED','exact_sku':sku})
  if row.get('pdp_vs_energyguide_model')=='NOT_COMPARABLE':
   gaps.append({'code':'ENERGYGUIDE_MODEL_UNRESOLVED','exact_sku':sku})
 for sku,row in sorted(indices.get('energy_star',{}).items()):
  if row.get('outcome')=='NOT_EVALUATED': gaps.append({'code':'ENERGY_STAR_UNRESOLVED','exact_sku':sku})
 return {'contract':'G3_DISHWASHER_FORMAL_READINESS_V1','status':'BLOCKED' if gaps else 'READY_FOR_ASSESSMENT',
         'sku_count':len(indices.get('energy_star',{})),'gaps':gaps}

def build(energy,numeric,model,out):
 es_source,nu_source,mo_source=load(energy),load(numeric),load(model)
 gate=readiness(es_source,nu_source,mo_source)
 d=Path(out);d.mkdir(parents=True,exist_ok=True)
 (d/'readiness.json').write_text(json.dumps(gate,indent=2)+'\n',encoding='utf-8')
 if gate['status']!='READY_FOR_ASSESSMENT':
  print(json.dumps({'status':'BLOCKED','sku_count':gate['sku_count'],
                    'gap_count':len(gate['gaps']),'gap_codes':dict(Counter(x['code'] for x in gate['gaps']))},sort_keys=True))
  return
 e={x['exact_sku']:x for x in es_source['records']}; n={x['exact_sku']:x for x in nu_source['rows']}; m={x['exact_sku']:x for x in mo_source['records']}
 if not e or set(e)!=set(n) or set(e)!=set(m): raise ValueError('Assessment SKU coverage differs')
 rows=[]; all_findings=[]
 for sku in sorted(e):
  es,nu,mo=e[sku],n[sku],m[sku]; f=[]
  if es.get('severity'): f.append({'control':'ENERGY_STAR_PUBLICATION','severity':es['severity'],'issue_code':es['issue_code']})
  # A mismatch requires the PDP to disagree with every listed EnergyGuide
  # pattern. One matching label pattern is sufficient for model identity.
  if mo['pdp_vs_energyguide_model']=='DIFFERENT' or mo['pdp_vs_epa_model']=='DIFFERENT' or (mo['energyguide_vs_epa_model']=='DIFFERENT' and mo['pdp_vs_energyguide_model']!='EQUAL'): f.append({'control':'MODEL_IDENTITY','severity':'HIGH','issue_code':'MODEL_IDENTITY_MISMATCH'})
  if mo['pdp_vs_epa_model']=='NOT_COMPARABLE': f.append({'control':'EPA_CURRENT','severity':'HIGH','issue_code':'EPA_CURRENT_MODEL_NOT_REGISTERED'})
  if nu['pdp_annual_energy'].get('state')=='NOT_OBSERVED': f.append({'control':'ANNUAL_ENERGY','severity':'LOW','issue_code':'PDP_ANNUAL_ENERGY_MISSING'})
  if 'DIFFERENT' in (nu['pdp_vs_energyguide_energy'],nu['energyguide_vs_epa_energy']): f.append({'control':'ANNUAL_ENERGY','severity':'MEDIUM','issue_code':'ANNUAL_ENERGY_MISMATCH'})
  f=sorted({(x['control'],x['severity'],x['issue_code']):x for x in f}.values(),key=lambda x:(x['control'],x['issue_code']))
  outcome=max((x['severity'] for x in f),key=RANK.__getitem__) if f else 'PASS'
  row={'exact_sku':sku,'display_outcome':outcome,'controls':{'energy_star_publication':{'outcome':es['outcome']},'energyguide_numeric':{'outcome':outcome,'comparisons':{k:nu[k] for k in ('pdp_vs_energyguide_energy','energyguide_vs_epa_energy')}},'energyguide_model':{'outcome':outcome,'comparisons':{k:mo[k] for k in ('pdp_vs_energyguide_model','pdp_vs_epa_model','energyguide_vs_epa_model')}}},'findings':f,'overall_product_compliance':'NOT_EVALUATED'}
  rows.append(row); all_findings += [{'exact_sku':sku,**x} for x in f]
 counts=Counter(x['display_outcome'] for x in rows)
 report={'contract':'G3_DISHWASHER_FINAL_ASSESSMENT_V1','status':'PASS','assessment_enabled':True,'sku_count':len(rows),'finding_count':len(all_findings),'affected_sku_count':len({x['exact_sku'] for x in all_findings}),'counts':{key:counts.get(key,0) for key in ('HIGH','MEDIUM','LOW','PASS')},'findings':all_findings,'rows':rows,'decision_rule':'Confirmed model mismatch or EPA Current absence HIGH; PDP annual missing LOW; confirmed annual mismatch MEDIUM; all other states PASS','overall_product_compliance':'NOT_EVALUATED'}
 md=['# G3 Dishwasher final assessment','',f"SKUs: **{len(rows)}** | HIGH: **{report['counts']['HIGH']}** | MEDIUM: **{report['counts']['MEDIUM']}** | LOW: **{report['counts']['LOW']}** | PASS: **{report['counts']['PASS']}**",'', '| Exact SKU | Result | PDP / Label model | PDP / EPA model | Label / EPA model | PDP / Label energy | Label / EPA energy | Findings |','|---|---|---|---|---|---|---|---|']
 details=[]
 for sku,row in zip(sorted(e),rows):
  nu,mo=n[sku],m[sku]
  labels=', '.join(mo.get('energyguide_model_patterns_raw',[])) or 'none observed';epa_models=', '.join(mo.get('epa_current_model_candidates_raw',[])) or 'none matched'
  md.append(f"| {sku} | {row['display_outcome']} | {mo['pdp_vs_energyguide_model']} | {mo['pdp_vs_epa_model']} | {mo['energyguide_vs_epa_model']} | {nu['pdp_vs_energyguide_energy']} | {nu['energyguide_vs_epa_energy']} | {', '.join(x['issue_code'] for x in row['findings']) or '—'} |")
  details.append({'exact_sku':sku,'outcome':row['display_outcome'],'energyguide_patterns_raw':mo.get('energyguide_model_patterns_raw',[]),'epa_models_raw':mo.get('epa_current_model_candidates_raw',[]),'model_comparisons':[mo[k] for k in ('pdp_vs_energyguide_model','pdp_vs_epa_model','energyguide_vs_epa_model')],'energy_comparisons':[nu[k] for k in ('pdp_vs_energyguide_energy','energyguide_vs_epa_energy')],'issue_codes':[f['issue_code'] for f in row['findings']]})
 (d/'assessment.json').write_text(json.dumps(report,indent=2)+'\n');(d/'assessment.md').write_text('\n'.join(md)+'\n');(d/'evidence-by-sku.json').write_text(json.dumps(details,indent=2)+'\n');summary=os.getenv('GITHUB_STEP_SUMMARY');Path(summary).write_text('\n'.join(md)+'\n',encoding='utf-8') if summary else None;print(json.dumps({'status':'PASS','sku_count':len(rows),'finding_count':len(all_findings),'counts':report['counts'],'by_sku':details},sort_keys=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--energy-star',required=True);p.add_argument('--numeric',required=True);p.add_argument('--model',required=True);p.add_argument('--out',required=True);a=p.parse_args();build(a.energy_star,a.numeric,a.model,a.out)

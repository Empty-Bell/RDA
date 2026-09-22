import argparse,json,os
from collections import Counter
from pathlib import Path
RANK={"LOW":1,"MEDIUM":2,"HIGH":3}
def load(p): return json.loads(Path(p).read_bytes())
def build(energy,numeric,model,out):
 e={x['exact_sku']:x for x in load(energy)['records']}; n={x['exact_sku']:x for x in load(numeric)['rows']}; m={x['exact_sku']:x for x in load(model)['records']}
 if not e or set(e)!=set(n) or set(e)!=set(m): raise ValueError('Assessment SKU coverage differs')
 rows=[]; all_findings=[]
 for sku in sorted(e):
  es,nu,mo=e[sku],n[sku],m[sku]; f=[]
  if es.get('severity'): f.append({'control':'ENERGY_STAR_PUBLICATION','severity':es['severity'],'issue_code':es['issue_code']})
  if 'DIFFERENT' in (mo['pdp_vs_energyguide_model'],mo['pdp_vs_epa_model'],mo['energyguide_vs_epa_model']): f.append({'control':'MODEL_IDENTITY','severity':'HIGH','issue_code':'MODEL_IDENTITY_MISMATCH'})
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
 d=Path(out);d.mkdir(parents=True,exist_ok=True);(d/'assessment.json').write_text(json.dumps(report,indent=2)+'\n');(d/'assessment.md').write_text('\n'.join(md)+'\n');(d/'evidence-by-sku.json').write_text(json.dumps(details,indent=2)+'\n');summary=os.getenv('GITHUB_STEP_SUMMARY');Path(summary).write_text('\n'.join(md)+'\n',encoding='utf-8') if summary else None;print(json.dumps({'status':'PASS','sku_count':len(rows),'finding_count':len(all_findings),'counts':report['counts'],'by_sku':details},sort_keys=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--energy-star',required=True);p.add_argument('--numeric',required=True);p.add_argument('--model',required=True);p.add_argument('--out',required=True);a=p.parse_args();build(a.energy_star,a.numeric,a.model,a.out)

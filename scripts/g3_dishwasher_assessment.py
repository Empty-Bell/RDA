import argparse,json
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
  if mo['pdp_vs_energyguide_model']=='DIFFERENT' or mo['energyguide_vs_epa_model']=='DIFFERENT': f.append({'control':'MODEL_IDENTITY','severity':'HIGH','issue_code':'ENERGYGUIDE_MODEL_IDENTITY_MISMATCH'})
  if mo['pdp_vs_epa_model']=='NOT_COMPARABLE': f.append({'control':'EPA_CURRENT','severity':'HIGH','issue_code':'EPA_CURRENT_MODEL_NOT_REGISTERED'})
  if nu['pdp_annual_energy'].get('state')=='NOT_OBSERVED': f.append({'control':'ANNUAL_ENERGY','severity':'LOW','issue_code':'PDP_ANNUAL_ENERGY_MISSING'})
  if 'DIFFERENT' in (nu['pdp_vs_energyguide_energy'],nu['energyguide_vs_epa_energy']): f.append({'control':'ANNUAL_ENERGY','severity':'MEDIUM','issue_code':'ANNUAL_ENERGY_MISMATCH'})
  f=sorted({(x['control'],x['severity'],x['issue_code']):x for x in f}.values(),key=lambda x:(x['control'],x['issue_code']))
  outcome=max((x['severity'] for x in f),key=RANK.__getitem__) if f else 'PASS'
  row={'exact_sku':sku,'display_outcome':outcome,'controls':{'energy_star_publication':{'outcome':es['outcome']},'energyguide_numeric':{'outcome':outcome,'comparisons':{k:nu[k] for k in ('pdp_vs_energyguide_energy','energyguide_vs_epa_energy')}},'energyguide_model':{'outcome':outcome,'comparisons':{k:mo[k] for k in ('pdp_vs_energyguide_model','pdp_vs_epa_model','energyguide_vs_epa_model')}}},'findings':f,'overall_product_compliance':'NOT_EVALUATED'}
  rows.append(row); all_findings += [{'exact_sku':sku,**x} for x in f]
 report={'contract':'G3_DISHWASHER_FINAL_ASSESSMENT_V1','status':'PASS','assessment_enabled':True,'sku_count':len(rows),'finding_count':len(all_findings),'affected_sku_count':len({x['exact_sku'] for x in all_findings}),'findings':all_findings,'rows':rows,'decision_rule':'Confirmed model/EPA absence HIGH; PDP annual missing LOW; confirmed annual mismatch MEDIUM; all other states PASS','overall_product_compliance':'NOT_EVALUATED'}
 d=Path(out);d.mkdir(parents=True,exist_ok=True);(d/'assessment.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','sku_count':len(rows),'finding_count':len(all_findings)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--energy-star',required=True);p.add_argument('--numeric',required=True);p.add_argument('--model',required=True);p.add_argument('--out',required=True);a=p.parse_args();build(a.energy_star,a.numeric,a.model,a.out)

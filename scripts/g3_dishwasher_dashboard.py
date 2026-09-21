"""Build a static source-coverage dashboard from one dishwasher comparison package."""
import argparse, csv, json
from pathlib import Path

def build(package_path, output):
    package=json.loads(Path(package_path).read_bytes())
    if package.get("contract")!="G3_DISHWASHER_COMPARISON_PACKAGE_V1" or package.get("status")!="PASS": raise ValueError("Invalid dishwasher comparison package")
    rows=[]
    for source in package.get("rows",[]):
        rows.append({"exact_sku":source["exact_sku"],"pdp_energy_observed":bool(source.get("pdp_energy_raw")),"pdp_capacity_observed":bool(source.get("pdp_capacity_raw")),"energyguide_candidate_count":len(source.get("energyguide_energy_candidates_raw",[])),"epa_match_status":source.get("epa_match_status"),"epa_candidate_count":len(source.get("epa_candidates_raw",[])),"assessment":"NOT_EVALUATED"})
    if len(rows)!=package.get("sku_count") or len({x["exact_sku"] for x in rows})!=len(rows): raise ValueError("Dashboard SKU coverage differs from comparison package")
    summary={"models_in_scope":len(rows),"pdp_energy_observed":sum(x["pdp_energy_observed"] for x in rows),"pdp_capacity_observed":sum(x["pdp_capacity_observed"] for x in rows),"energyguide_candidates_observed":sum(x["energyguide_candidate_count"]>0 for x in rows),"epa_matched":sum(x["epa_match_status"]=="MATCHED_CURRENT_EPA_ROW" for x in rows),"assessment":"NOT_EVALUATED"}
    out=Path(output); data=out/"data"; data.mkdir(parents=True,exist_ok=True)
    for name,value in [("summary.json",summary),("report-data.json",rows),("methodology.json",{"scope":"Dishwasher source coverage only","assessment":"NOT_EVALUATED","source_contract":package["contract"]})]: (data/name).write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")
    with (out/"report-data.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ["exact_sku"]); w.writeheader(); w.writerows(rows)
    (out/"index.html").write_text("""<!doctype html><meta charset=utf-8><title>Dishwasher source coverage</title><main><h1>Dishwasher source coverage</h1><pre id=s></pre><input id=q placeholder='SKU search'><table><thead><tr><th>SKU</th><th>PDP energy</th><th>PDP capacity</th><th>Label candidates</th><th>EPA status</th></tr></thead><tbody id=t></tbody></table></main><script>Promise.all(['data/summary.json','data/report-data.json'].map(x=>fetch(x).then(x=>x.json()))).then(([s,d])=>{document.querySelector('#s').textContent=JSON.stringify(s,null,2);let draw=()=>t.innerHTML=d.filter(x=>x.exact_sku.includes(q.value.toUpperCase())).map(x=>`<tr><td>${x.exact_sku}</td><td>${x.pdp_energy_observed}</td><td>${x.pdp_capacity_observed}</td><td>${x.energyguide_candidate_count}</td><td>${x.epa_match_status}</td></tr>`).join('');q.oninput=draw;draw()})</script>""",encoding="utf-8")
    print(json.dumps({"status":"PASS",**summary},sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--package",required=True);p.add_argument("--out",required=True);a=p.parse_args();build(a.package,a.out)

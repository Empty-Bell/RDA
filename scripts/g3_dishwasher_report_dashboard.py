"""Build a static dashboard from the canonical dishwasher report."""
import argparse,csv,json
from pathlib import Path
def build(report_path,out):
 r=json.loads(Path(report_path).read_bytes())
 if r.get("contract")!="G3_DISHWASHER_CANONICAL_REPORT_V1" or r.get("status")!="PASS":raise ValueError("Invalid canonical dishwasher report")
 rows=[];findings=[]
 for x in r["rows"]:
  es=x["controls"]["energy_star_publication"]["outcome"]; num=x["controls"]["energyguide_numeric"]
  rows.append({"exact_sku":x["exact_sku"],"energy_star_publication":es,"energyguide_numeric":num["outcome"],"pdp_vs_energyguide_energy":num["comparisons"]["pdp_vs_energyguide_energy"],"energyguide_vs_epa_energy":num["comparisons"]["energyguide_vs_epa_energy"],"finding_count":len(x["findings"])})
  findings += [{"exact_sku":x["exact_sku"],**f} for f in x["findings"]]
 if len(rows)!=r["sku_count"]:raise ValueError("Dashboard coverage differs from canonical report")
 summary={"models_in_scope":len(rows),"finding_count":len(findings),"affected_sku_count":len({x["exact_sku"] for x in findings}),"findings_by_severity":{s:sum(x["severity"]==s for x in findings) for s in ("HIGH","MEDIUM","LOW")},"overall_product_compliance":"NOT_EVALUATED"}
 out=Path(out);data=out/"data";data.mkdir(parents=True,exist_ok=True)
 for n,v in [("summary.json",summary),("report-data.json",rows),("findings.json",findings),("methodology.json",{"scope":"Dishwasher canonical report dashboard","overall_product_compliance":"NOT_EVALUATED"})]:(data/n).write_text(json.dumps(v,indent=2)+"\n",encoding="utf-8")
 with (out/"report-data.csv").open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ["exact_sku"]);w.writeheader();w.writerows(rows)
 with (out/"findings.csv").open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=["exact_sku","control","severity","issue_code"]);w.writeheader();w.writerows(findings)
 (out/"index.html").write_text("""<!doctype html><meta charset=utf-8><title>Dishwasher regulatory audit</title><main><h1>Dishwasher regulatory audit</h1><pre id=s></pre><label>SKU <input id=q></label><table><thead><tr><th>SKU</th><th>Energy Star</th><th>PDP / Label energy</th><th>Label / EPA energy</th><th>Findings</th></tr></thead><tbody id=t></tbody></table></main><script>Promise.all(['data/summary.json','data/report-data.json'].map(x=>fetch(x).then(x=>x.json()))).then(([s,d])=>{document.querySelector('#s').textContent=JSON.stringify(s,null,2);let draw=()=>t.innerHTML=d.filter(x=>x.exact_sku.includes(q.value.toUpperCase())).map(x=>`<tr><td>${x.exact_sku}</td><td>${x.energy_star_publication}</td><td>${x.pdp_vs_energyguide_energy}</td><td>${x.energyguide_vs_epa_energy}</td><td>${x.finding_count}</td></tr>`).join('');q.oninput=draw;draw()})</script>""",encoding="utf-8")
 print(json.dumps({"status":"PASS",**summary},sort_keys=True))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--report",required=True);p.add_argument("--out",required=True);a=p.parse_args();build(a.report,a.out)

"""Combine dishwasher Energy Star and numeric controls into one canonical report."""
import argparse,json
from pathlib import Path
def build(energy_star,numeric,out):
    es=json.loads(Path(energy_star).read_bytes()); nu=json.loads(Path(numeric).read_bytes())
    a={x["exact_sku"]:x for x in es.get("records",[])}; b={x["exact_sku"]:x for x in nu.get("rows",[])}
    if not a or set(a)!=set(b): raise ValueError("Dishwasher control SKU coverage differs")
    rows=[]; findings=[]
    for sku in sorted(a):
        e=a[sku]; n=b[sku]; f=[]
        if e.get("issue_code"): f.append({"control":"ENERGY_STAR_PUBLICATION","severity":e["severity"],"issue_code":e["issue_code"]})
        findings += [{"exact_sku":sku,**x} for x in f]
        rows.append({"exact_sku":sku,"controls":{"energy_star_publication":{"outcome":e["outcome"]},"energyguide_numeric":{"outcome":"NOT_EVALUATED","comparisons":{k:n[k] for k in ("pdp_vs_energyguide_energy","energyguide_vs_epa_energy","pdp_vs_epa_place_settings")}}},"findings":f,"overall_product_compliance":"NOT_EVALUATED"})
    report={"contract":"G3_DISHWASHER_CANONICAL_REPORT_V1","status":"PASS","assessment_enabled":False,"sku_count":len(rows),"finding_count":len(findings),"affected_sku_count":len({x["exact_sku"] for x in findings}),"findings":findings,"rows":rows,"overall_product_compliance":"NOT_EVALUATED"}
    p=Path(out);p.mkdir(parents=True,exist_ok=True);(p/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps({"status":"PASS","sku_count":len(rows),"finding_count":len(findings)},sort_keys=True))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--energy-star",required=True);p.add_argument("--numeric",required=True);p.add_argument("--out",required=True);a=p.parse_args();build(a.energy_star,a.numeric,a.out)

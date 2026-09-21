"""Assemble same-SKU PDP, EnergyGuide, and EPA source observations."""
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

def load(path): return json.loads(Path(path).read_bytes())

def build(pdp_root, observation_root, epa_root, match_root, out):
    products = {x["exact_sku"]: x for x in load(Path(pdp_root)/"products.json")}
    results = {x["exact_sku"]: x for x in [load(p) for p in Path(pdp_root).glob("pdp/*/result.json")]}
    obs = load(Path(observation_root)/"sku-document-index.json")
    o_by_sku = {}
    for x in obs.get("sku_documents", []): o_by_sku.setdefault(x["exact_sku"], []).append(x)
    epa = load(Path(epa_root)/"samsung-current-rows.json")
    match = load(Path(match_root)/"match-report.json")
    m_by_sku = {x["exact_sku"]:x for x in match.get("rows", [])}
    epa_by_id = {str(x.get("pd_id")): x for x in epa}
    rows=[]
    for sku in sorted(products):
        result=results.get(sku, {}); facts=result.get("pdp_facts_raw", {})
        candidates=[]
        for doc in o_by_sku.get(sku, []):
            p=Path(observation_root)/"pdf"/doc["pdf_sha256"]/"observation.json"
            if not p.is_file(): continue
            ob=load(p)
            for page in ob.get("pages", []):
                fields=page.get("fields_raw") or {}
                candidates += [{"pdf_sha256":doc["pdf_sha256"],"page":page.get("page"),**x} for x in fields.get("energy_candidates_raw", [])]
        m=m_by_sku.get(sku,{})
        epa_rows=[epa_by_id[str(x)] for x in m.get("candidate_pd_ids",[]) if str(x) in epa_by_id]
        rows.append({"exact_sku":sku,"pdp_energy_raw":facts.get("energy_consumption_raw",[]),"pdp_capacity_raw":facts.get("capacity_raw",[]),"energyguide_energy_candidates_raw":candidates,"epa_candidates_raw":epa_rows,"epa_match_status":m.get("match_status","NOT_OBSERVED"),"comparison_status":"REVIEW_REQUIRED","assessment":"NOT_EVALUATED"})
    report={"contract":"G3_DISHWASHER_COMPARISON_PACKAGE_V1","created_at":datetime.now(timezone.utc).isoformat(),"scope":"Same-SKU source observation package only; no field selection, tolerance, finding, or compliance assessment","status":"PASS","sku_count":len(rows),"rows":rows}
    Path(out).mkdir(parents=True,exist_ok=True); Path(out,"comparison-package.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","sku_count":len(rows)},sort_keys=True))

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--pdp-root",required=True); p.add_argument("--observation-root",required=True); p.add_argument("--epa-root",required=True); p.add_argument("--match-root",required=True); p.add_argument("--out",required=True); a=p.parse_args(); build(a.pdp_root,a.observation_root,a.epa_root,a.match_root,a.out)

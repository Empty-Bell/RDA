"""Apply the approved three-point Energy Star rule to dishwasher source inputs."""
import argparse, json
from pathlib import Path

LOW_ISSUE="SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT"
HIGH_ISSUE="CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE"

def point(value): return {"state":{"Y":"PRESENT","N":"ABSENT"}.get(value,"UNKNOWN"),"raw_value":value}
def spec(rows):
    rows=[x for x in rows or [] if "energy star" in str(x.get("name","")).lower() and "certif" in str(x.get("name","")).lower()]
    if not rows:return {"state":"ABSENT","raw_rows":[]}
    values={str(x.get("value","")).strip().lower() for x in rows}
    return {"state":"PRESENT" if values and values<={"yes","y","true"} else "ABSENT" if values and values<={"no","n","false"} else "UNKNOWN","raw_rows":rows}
def pdp_flag(claim):
    values=[x.get("value") for x in claim.get("pdp_nested_energy_star_fields_raw",[]) if x.get("name")=="energyStarFlag"]
    values=list(dict.fromkeys(values)); return values[0] if len(values)==1 else None

def build(collection_root, match_path, out):
    results=[json.loads(p.read_bytes()) for p in Path(collection_root).glob("pdp/*/result.json")]
    match=json.loads(Path(match_path).read_bytes()); matches={x["exact_sku"]:x for x in match.get("rows",[])}
    records=[]
    for result in sorted(results,key=lambda x:x["exact_sku"]):
        sku=result["exact_sku"]; claim=result.get("energy_star_claim_sources_raw") or {}; m=matches.get(sku,{})
        points={"plp_logo":point(claim.get("plp_energy_star_flag_raw")),"pdp_logo":point(pdp_flag(claim)),"spec_certification":spec(claim.get("pdp_spec_energy_star_claim_raw"))}
        reg="PRESENT" if m.get("match_status") in {"MATCHED_CURRENT_EPA_ROW", "MATCHED_CURRENT_EPA_PATTERN_CANDIDATES"} else "ABSENT" if m.get("match_status")=="NO_CURRENT_EPA_ROW" else "UNKNOWN"
        states=[x["state"] for x in points.values()]
        if reg=="PRESENT" and all(x=="PRESENT" for x in states): outcome,severity,issue="PASS",None,None
        elif reg=="PRESENT" and "ABSENT" in states: outcome,severity,issue="LOW","LOW",LOW_ISSUE
        elif reg=="ABSENT" and "PRESENT" in states: outcome,severity,issue="HIGH","HIGH",HIGH_ISSUE
        elif reg=="ABSENT" and all(x=="ABSENT" for x in states): outcome,severity,issue="NO_FINDING",None,None
        else: outcome,severity,issue="NOT_EVALUATED",None,None
        records.append({"exact_sku":sku,"epa_current_registration":{"state":reg,"match_status":m.get("match_status"),"candidate_pd_ids":m.get("candidate_pd_ids",[])},"publication_points":points,"outcome":outcome,"severity":severity,"issue_code":issue})
    counts={x:sum(r["outcome"]==x for r in records) for x in ("PASS","LOW","HIGH","NO_FINDING","NOT_EVALUATED")}
    report={"contract":"G3_DISHWASHER_ENERGY_STAR_ASSESSMENT_V1","status":"PASS","scope":"Exact-SKU PF, PDP Next, Bridge Specs and current EPA row candidates","rule":{"registered_all_three_present":"PASS","registered_any_absent":"LOW","unregistered_any_present":"HIGH","unregistered_all_absent":"NO_FINDING","unknown":"NOT_EVALUATED"},"counts":counts,"records":records,"overall_product_compliance":"NOT_EVALUATED"}
    target=Path(out);target.mkdir(parents=True,exist_ok=True);(target/"energy-star-assessment.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps({"status":"PASS","counts":counts},sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--collection-root",required=True);p.add_argument("--match",required=True);p.add_argument("--out",required=True);a=p.parse_args();build(a.collection_root,a.match,a.out)

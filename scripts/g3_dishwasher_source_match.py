"""Join exact dishwasher SKUs to current EPA rows without issuing a compliance result."""
import argparse, json, re
from datetime import datetime, timezone
from pathlib import Path

def j(path): return json.loads(Path(path).read_bytes())
def norm(value):
    value = re.sub(r"[^A-Z0-9]", "", str(value or "").upper())
    return re.sub(r"AA$", "", value)

def build(observation_root, epa_root, out):
    obs = j(Path(observation_root) / "sku-document-index.json")
    epa = j(Path(epa_root) / "samsung-current-rows.json")
    if not isinstance(epa, list): raise ValueError("EPA rows are not a list")
    by_model = {}
    for row in epa:
        model = row.get("model_number")
        if model: by_model.setdefault(norm(model), []).append(row)
    skus = sorted({x["exact_sku"] for x in obs.get("sku_documents", [])})
    rows = []
    for sku in skus:
        candidates = by_model.get(norm(sku), [])
        rows.append({"exact_sku": sku, "normalized_sku": norm(sku),
                     "candidate_count": len(candidates),
                     "candidate_pd_ids": [x.get("pd_id") for x in candidates],
                     "candidate_model_numbers": [x.get("model_number") for x in candidates],
                     "match_status": "MATCHED_CURRENT_EPA_ROW" if len(candidates)==1 else "AMBIGUOUS_CURRENT_EPA_ROWS" if candidates else "NO_CURRENT_EPA_ROW",
                     "assessment": "NOT_EVALUATED"})
    report = {"contract":"G3_DISHWASHER_CURRENT_EPA_MATCH_V1", "created_at":datetime.now(timezone.utc).isoformat(),
              "scope":"Exact normalized SKU to current EPA row candidate projection only; no certification or compliance assessment",
              "status":"PASS", "sku_count":len(rows), "epa_row_count":len(epa),
              "counts":{s:sum(x["match_status"]==s for x in rows) for s in ("MATCHED_CURRENT_EPA_ROW","NO_CURRENT_EPA_ROW","AMBIGUOUS_CURRENT_EPA_ROWS")},
              "rows":rows}
    Path(out).mkdir(parents=True, exist_ok=True)
    Path(out, "match-report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status":"PASS", **report["counts"]}, sort_keys=True))

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--observation-root",required=True); p.add_argument("--epa-root",required=True); p.add_argument("--out",required=True); a=p.parse_args(); build(a.observation_root,a.epa_root,a.out)

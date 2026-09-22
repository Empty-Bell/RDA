"""Compare exact dishwasher SKUs to raw EnergyGuide model patterns."""
import argparse,json,re
from pathlib import Path
def normalized(value):
 value=re.sub(r"[^A-Z0-9]","",str(value).upper())
 return value[:-2] if value.endswith("AA") else value
def matches(sku,pattern):
 sku,pattern=normalized(sku),normalized(pattern)
 return bool(pattern and re.fullmatch("".join("[A-Z0-9]" if c in "*?" else re.escape(c) for c in pattern),sku))
def build(package,out):
 source=json.loads(Path(package).read_bytes());rows=[]
 for item in source.get("rows",[]):
  patterns=sorted({x.get("value_raw") for x in item.get("energyguide_model_candidates_raw",[]) if isinstance(x.get("value_raw"),str)})
  included=[x for x in patterns if matches(item["exact_sku"],x)]
  outcome="PASS" if included else "NOT_INCLUDED" if patterns else "NOT_EVALUATED"
  rows.append({"exact_sku":item["exact_sku"],"normalized_exact_sku":normalized(item["exact_sku"]),"model_patterns_raw":patterns,"matching_patterns":included,"outcome":outcome,"assessment":"NOT_EVALUATED"})
 report={"contract":"G3_DISHWASHER_ENERGYGUIDE_MODEL_COMPARISON_V1","status":"PASS","scope":"Exact SKU to raw EnergyGuide model pattern inclusion; no severity or compliance assessment","counts":{s:sum(x["outcome"]==s for x in rows) for s in ("PASS","NOT_INCLUDED","NOT_EVALUATED")},"records":rows}
 p=Path(out);p.mkdir(parents=True,exist_ok=True);(p/"model-comparison.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps({"status":"PASS","counts":report["counts"]},sort_keys=True))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--package",required=True);p.add_argument("--out",required=True);a=p.parse_args();build(a.package,a.out)

"""Select conservative dishwasher source values and compare them without findings."""
import argparse, json, re
from decimal import Decimal, InvalidOperation
from pathlib import Path

def number(value):
    try: return str(Decimal(str(value).replace(",", "").strip()).normalize())
    except (InvalidOperation, AttributeError): return None

def unique(values):
    clean=sorted({x for x in values if x is not None})
    return {"state":"VALUE","value":clean[0]} if len(clean)==1 else {"state":"NOT_OBSERVED" if not clean else "AMBIGUOUS","candidates":clean}

def build(package_path, out):
    package=json.loads(Path(package_path).read_bytes())
    if package.get("contract")!="G3_DISHWASHER_COMPARISON_PACKAGE_V1" or package.get("status")!="PASS": raise ValueError("Invalid dishwasher comparison package")
    rows=[]
    for row in package.get("rows",[]):
        pdp_energy=unique([number(x.get("value")) for x in row.get("pdp_energy_raw",[])])
        label_energy=unique([number(x.get("value_raw")) for x in row.get("energyguide_energy_candidates_raw",[]) if x.get("role")=="ANNUAL_CAPTION_CONTEXT"])
        epa_energy=unique([number(x.get("annual_energy_use_kwh_year")) for x in row.get("epa_candidates_raw",[])])
        def compare(a,b):
            if a.get("state")!="VALUE" or b.get("state")!="VALUE": return "NOT_COMPARABLE"
            return "EQUAL" if a["value"]==b["value"] else "DIFFERENT"
        rows.append({"exact_sku":row["exact_sku"],"pdp_annual_energy":pdp_energy,"energyguide_annual_energy":label_energy,"epa_annual_energy":epa_energy,"pdp_vs_energyguide_energy":compare(pdp_energy,label_energy),"energyguide_vs_epa_energy":compare(label_energy,epa_energy),"assessment":"NOT_EVALUATED","findings":[]})
    counts={key:{state:sum(x[key]==state for x in rows) for state in ("EQUAL","DIFFERENT","NOT_COMPARABLE")} for key in ("pdp_vs_energyguide_energy","energyguide_vs_epa_energy")}
    report={"contract":"G3_DISHWASHER_NUMERIC_COMPARISON_V2","source_contract":package["contract"],"status":"PASS","scope":"Annual-energy source comparisons only; dishwasher capacity and place-settings values are excluded as non-comparable, with no tolerance, severity, findings, or compliance assessment","sku_count":len(rows),"counts":counts,"rows":rows,"assessment":"NOT_EVALUATED"}
    target=Path(out);target.mkdir(parents=True,exist_ok=True);(target/"numeric-comparison.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","sku_count":len(rows),"counts":counts},sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--package",required=True);p.add_argument("--out",required=True);a=p.parse_args();build(a.package,a.out)

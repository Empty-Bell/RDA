"""Explain why failed TV PDP results did not pass same-SKU evidence checks."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from urllib.parse import quote, urlsplit

from source_contract import pdp_facts


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def diagnose(root, sku):
    folder = root / "pdp" / quote(sku, safe="")
    record = read(folder / "result.json")
    snapshot_path = folder / "snapshot.json"
    snapshot = read(snapshot_path) if snapshot_path.is_file() else {}
    checks = []
    parts = urlsplit(record.get("final_url", ""))
    expected_slug = re.escape(sku.lower().replace("/", "-"))
    if not (parts.scheme == "https" and parts.hostname == "www.samsung.com" and "/us/" in parts.path and re.search(r"-sku-" + expected_slug + r"/?$", parts.path.lower())):
        checks.append("final_url_wrong_sku_or_missing")
    if snapshot.get("jsonld_parse_errors"):
        checks.append("jsonld_parse_error")
    declarations = snapshot.get("product_jsonld")
    if not isinstance(declarations, list) or not declarations:
        checks.append("no_product_jsonld")
    else:
        identity_rows = [[d.get(k) for k in ("sku", "mpn") if d.get(k)] for d in declarations]
        if any(not identities for identities in identity_rows):
            checks.append("product_jsonld_identity_missing")
        elif any(value != sku for identities in identity_rows for value in identities):
            checks.append("product_jsonld_exact_sku_mismatch")
    responses = record.get("bridge_responses", [])
    if not responses:
        checks.append("no_specs_support_bridge_response")
    elif not any(entry.get("path") for entry in responses):
        checks.append("bridge_response_unusable")
    else:
        fact_errors = []
        for entry in responses:
            relative = entry.get("path")
            if not relative:
                continue
            bridge_path = folder / relative
            if not bridge_path.is_file():
                fact_errors.append("bridge_file_missing")
                continue
            try:
                pdp_facts(read(bridge_path), sku, family="tv")
            except Exception as error:
                fact_errors.append(str(error).splitlines()[0][:160])
            else:
                fact_errors.append("bridge_exact_sku_facts_valid")
        checks.extend("bridge:" + reason for reason in fact_errors)
    return {"exact_sku": sku, "error": record.get("error"), "http_status": record.get("http_status"),
            "requested_url": record.get("requested_url"), "final_url": record.get("final_url"),
            "bridge_responses": [{"status": e.get("status"), "has_projected_payload": bool(e.get("path")),
                                  "error_class": e.get("error_class")} for e in responses],
            "jsonld_parse_errors": snapshot.get("jsonld_parse_errors"),
            "product_jsonld": snapshot.get("product_jsonld", []),
            "diagnostic_checks": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root, out = Path(args.collection_root), Path(args.out)
    summary = read(root / "collection-summary.json")
    failed = [row["exact_sku"] for row in summary["coverage"]["rows"] if row["status"] == "FAILED"]
    records = [diagnose(root, sku) for sku in failed]
    reasons = Counter(check for record in records for check in record["diagnostic_checks"])
    result = {"collection_run_id": summary.get("collection_run_id"), "population_count": summary["coverage"]["population_count"],
              "failed_count": len(records), "diagnostic_reason_counts": dict(reasons), "examples": records[:12], "rows": records}
    out.mkdir(parents=True, exist_ok=True)
    (out / "pdp-diagnostics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("collection_run_id", "population_count", "failed_count", "diagnostic_reason_counts", "examples")}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

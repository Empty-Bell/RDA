"""Assemble the original successful TV captures plus the latest retry outcomes."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
from urllib.parse import quote


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-root", required=True)
    parser.add_argument("--shards-root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--allow-unverified", action="store_true",
                        help="Return success when every SKU was attempted, even if exact identity failed")
    args = parser.parse_args()
    original, shards, out = Path(args.original_root), Path(args.shards_root), Path(args.out)
    base = load(original / "collection-summary.json")
    if base.get("status") != "FAILED":
        raise ValueError("Recovery aggregate expects an initially failed collection")
    out.mkdir(parents=True, exist_ok=True)
    (out / "pdp").mkdir(exist_ok=True)
    shutil.copy2(original / "population.json", out / "population.json")
    shutil.copy2(original / "products.json", out / "products.json")
    rows = {r["exact_sku"]: dict(r) for r in base["coverage"]["rows"]}
    products = {p["exact_sku"]: p for p in load(original / "products.json")}
    selected_roots = []
    for summary_path in shards.glob("g3-tv-retry-*/retry-summary.json"):
        report = load(summary_path)
        selected_roots.append(summary_path.parent)
        for result in report["rows"]:
            sku = result["exact_sku"]
            if sku not in rows or rows[sku]["status"] not in ("FAILED", "NOT_ATTEMPTED"):
                raise ValueError(f"Retry contains an unexpected or originally successful SKU: {sku}")
            rows[sku] = {"exact_sku": sku, "status": result["status"], **({"error": result["error"]} if result.get("error") else {})}
    # Retain each original success, and the latest retry result for every failed SKU.
    for sku, result in rows.items():
        source = original / "pdp" / quote(sku, safe="")
        if sku in products and base["coverage"]["rows"]:
            orig_row = next(r for r in base["coverage"]["rows"] if r["exact_sku"] == sku)
            if orig_row["status"] == "VERIFIED_EXACT_IDENTITY":
                pass
            else:
                source = next((root / "pdp" / quote(sku, safe="") for root in selected_roots
                               if (root / "pdp" / quote(sku, safe="") / "result.json").is_file()), source)
        if source is None or not (source / "result.json").is_file():
            if result["status"] == "NOT_ATTEMPTED":
                continue
            raise ValueError(f"Evidence folder missing for {sku}")
        shutil.copytree(source, out / "pdp" / quote(sku, safe=""))
    counts = Counter(row["status"] for row in rows.values())
    rows_list = [rows[sku] for sku in sorted(rows)]
    status = "PASS" if counts["FAILED"] == 0 and counts["NOT_ATTEMPTED"] == 0 else "FAILED"
    report = dict(base)
    report.update(collection_run_id=os.getenv("GITHUB_RUN_ID"),
                  recovery_of_collection_run_id=base.get("collection_run_id"),
                  captured_at=datetime.now(timezone.utc).isoformat(), status=status,
                  coverage={"population_count": len(rows_list), "attempted_count": len(rows_list),
                            "counts": {state: counts[state] for state in ("VERIFIED_EXACT_IDENTITY", "FAILED", "NOT_ATTEMPTED")},
                            "rows": rows_list})
    (out / "collection-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reasons = Counter(row.get("error", "(no error detail)") for row in rows_list if row["status"] == "FAILED")
    print(json.dumps({"status": status, "population_count": len(rows_list), "coverage_counts": report["coverage"]["counts"], "failure_reasons": dict(reasons)}, sort_keys=True), flush=True)
    complete = counts["NOT_ATTEMPTED"] == 0
    return 0 if status == "PASS" or (args.allow_unverified and complete) else 1


if __name__ == "__main__":
    raise SystemExit(main())

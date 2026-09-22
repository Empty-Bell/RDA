"""Collect one deterministic shard of the exact-SKU TV PDP population."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from g3_tv_collect import collect, coverage, load_population


def shard_for(sku, count):
    return int.from_bytes(hashlib.sha256(sku.encode("utf-8")).digest()[:4], "big") % count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recon-root", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--shard-index", required=True, type=int)
    parser.add_argument("--shard-count", required=True, type=int)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise ValueError("Invalid TV collection shard coordinates")
    products, population = load_population(args.recon_root, args.source_run_id)
    selected = [p for p in products if shard_for(p["exact_sku"], args.shard_count) == args.shard_index]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "population.json").write_text(json.dumps(population, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "products.json").write_text(json.dumps(selected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    results = collect(selected, out)
    rows = coverage(selected, results)
    errors = Counter(row.get("error", "(no error detail)") for row in rows["rows"] if row["status"] == "FAILED")
    summary = {"source_run_id": str(args.source_run_id), "shard_index": args.shard_index,
               "shard_count": args.shard_count, "population_count": len(selected),
               "coverage_counts": rows["counts"], "failure_reasons": dict(errors), "rows": results}
    (out / "shard-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("shard_index", "shard_count", "population_count", "coverage_counts", "failure_reasons")}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

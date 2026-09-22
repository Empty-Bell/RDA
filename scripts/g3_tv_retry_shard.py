"""Retry a deterministic shard of failed SKUs from a TV collection artifact."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from g3_tv_collect import collect


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root, out = Path(args.collection_root), Path(args.out)
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise ValueError("Invalid shard coordinates")
    products = load(root / "products.json")
    summary = load(root / "collection-summary.json")
    if summary.get("status") != "FAILED":
        raise ValueError("Recovery expects a failed source collection")
    failed = {row["exact_sku"] for row in summary["coverage"]["rows"]
              if row["status"] in ("FAILED", "NOT_ATTEMPTED")}
    selected = [p for p in products
                if p["exact_sku"] in failed and
                (int.from_bytes(hashlib.sha256(p["exact_sku"].encode("utf-8")).digest()[:4], "big")
                 % args.shard_count) == args.shard_index]
    out.mkdir(parents=True, exist_ok=True)
    results = collect(selected, out)
    counts = Counter(row["status"] for row in results)
    errors = Counter(row.get("error", "(no error detail)") for row in results if row["status"] == "FAILED")
    report = {"source_collection_run_id": summary.get("collection_run_id"),
              "shard_index": args.shard_index, "shard_count": args.shard_count,
              "population_count": len(selected), "counts": dict(counts),
              "failure_reasons": dict(errors), "rows": results}
    (out / "retry-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("shard_index", "shard_count", "population_count", "counts", "failure_reasons")}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

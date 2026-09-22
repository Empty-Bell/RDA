"""Assemble matrix-collected TV PDP shards into the downstream artifact contract."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
from urllib.parse import quote

from g3_tv_collect import coverage, load_population
from g3_tv_collect_shard import shard_for


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recon-root", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--shards-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    products, population = load_population(args.recon_root, args.source_run_id)
    shards, out = Path(args.shards_root), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "pdp").mkdir(exist_ok=True)
    results, seen_shards = [], set()
    for summary_path in sorted(shards.glob("g3-tv-collection-shard-*/shard-summary.json")):
        shard_root = summary_path.parent
        shard = read(summary_path)
        index, count = shard["shard_index"], shard["shard_count"]
        if count != 8 or index in seen_shards:
            raise ValueError("Missing, duplicate, or invalid TV collection shard")
        seen_shards.add(index)
        for record in shard["rows"]:
            sku = record.get("exact_sku")
            if shard_for(sku, count) != index:
                raise ValueError(f"Exact SKU was assigned to the wrong shard: {sku}")
            results.append(record)
            source = shard_root / "pdp" / quote(sku, safe="")
            if not (source / "result.json").is_file():
                raise ValueError(f"Shard evidence is missing for {sku}")
            shutil.copytree(source, out / "pdp" / quote(sku, safe=""))
    rows = coverage(products, results)
    counts = Counter(row["error"] for row in rows["rows"] if row["status"] == "FAILED")
    status = "PASS" if rows["counts"]["FAILED"] == 0 and rows["counts"]["NOT_ATTEMPTED"] == 0 else "FAILED"
    (out / "population.json").write_text(json.dumps(population, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "products.json").write_text(json.dumps(products, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {"contract": "G3_TV_EXACT_SKU_PDP_V1", "source_run_id": str(args.source_run_id),
              "collection_run_id": os.getenv("GITHUB_RUN_ID"), "git_sha": os.getenv("GITHUB_SHA"),
              "captured_at": datetime.now(timezone.utc).isoformat(),
              "scope": "TV exact-SKU PDP identity and source facts only; no matching or assessment",
              "assessment": "NOT_EVALUATED", "population": population, "coverage": rows, "status": status}
    (out / "collection-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "population_count": rows["population_count"],
                      "coverage_counts": rows["counts"], "missing_shards": sorted(set(range(8)) - seen_shards),
                      "failure_reasons": dict(counts)}, sort_keys=True), flush=True)
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        with Path(summary_file).open("a", encoding="utf-8") as stream:
            stream.write("## TV exact-SKU PDP collection\n\n")
            stream.write(f"Status: **{status}**; population: {rows['population_count']}\n\n")
            stream.write(f"Coverage: `{json.dumps(rows['counts'], sort_keys=True)}`\n\n")
            for error, count in counts.most_common():
                stream.write(f"- {count} SKU(s): {error}\n")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

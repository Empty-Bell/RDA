"""Quarantine a bounded number of unverifiable exact SKUs (approved 2026-10-27).

After every bounded and deferred retry, an exact SKU whose PDP identity still
cannot be verified is not graded. It is moved out of the collection the
assessment reads, its raw capture is preserved under ``quarantine/``, and it is
reported as UNVERIFIED. It never becomes PASS. When a family has more failures
than the allowance, or any SKU was not attempted, the family fails as before.
"""

import json
import math
import os
from pathlib import Path
import shutil
from urllib.parse import quote


CONTRACT = "RDA_SKU_QUARANTINE_V1"
MAX_UNVERIFIED = 2
MAX_SHARE = 0.05
DRILL_ENV = "RDA_QUARANTINE_DRILL"
DRILL_ERROR = "QUARANTINE_DRILL_SIMULATED_FAILURE"


class QuarantineRefused(ValueError):
    pass


def allowance(population_count):
    """At most two SKUs and at most 5% (rounded up) of the family population."""
    if not isinstance(population_count, int) or population_count < 1:
        raise QuarantineRefused("Quarantine needs a positive exact-SKU population")
    return min(MAX_UNVERIFIED, math.ceil(population_count * MAX_SHARE))


def drill_enabled():
    if os.getenv(DRILL_ENV, "").strip().lower() not in {"1", "true"}:
        return False
    if os.getenv("GITHUB_REF", "") == "refs/heads/main":
        raise QuarantineRefused("A quarantine drill must never run on main")
    return True


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _entry(sku, result, error):
    result = result or {}
    listing = result.get("source_claim_listing_raw") or result.get("listing_raw") or {}
    return {"exact_sku": sku, "status": "UNVERIFIED", "error": error or result.get("error"),
            "requested_url": result.get("requested_url"), "final_url": result.get("final_url"),
            "http_status": result.get("http_status"),
            "plp_stock_flag_raw": listing.get("stockFlag") if isinstance(listing, dict) else None}


def _check(failed, population_count, not_attempted):
    if not_attempted:
        raise QuarantineRefused("Exact SKUs were not attempted; the family collection is incomplete")
    limit = allowance(population_count)
    if len(failed) > limit:
        raise QuarantineRefused(
            f"{len(failed)} unverifiable exact SKUs exceed the allowance of {limit} "
            f"for a population of {population_count}")


def _move_capture(pdp_root, sku, target):
    source = Path(pdp_root) / quote(sku, safe="")
    if source.is_dir():
        target = Path(target) / quote(sku, safe="")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        return str(target)
    return None


def _drill_target(skus):
    return sorted(skus)[0] if drill_enabled() and skus else None


def quarantine_single(collection, quarantine_root):
    """Quarantine failed rows of a single ``collection-summary.json`` collection."""
    collection, quarantine_root = Path(collection), Path(quarantine_root)
    summary = read(collection / "collection-summary.json")
    coverage = summary.get("coverage") or {}
    rows = coverage.get("rows")
    population = coverage.get("population_count")
    if not isinstance(rows, list) or len(rows) != population:
        raise QuarantineRefused("Collection coverage rows do not match its population")
    drill = None
    if summary.get("status") == "PASS":
        drill = _drill_target([row["exact_sku"] for row in rows if row.get("status") == "VERIFIED_EXACT_IDENTITY"])
        if not drill:
            return []
    elif summary.get("status") != "FAILED":
        raise QuarantineRefused("Collection status is neither PASS nor FAILED")
    failed = {row["exact_sku"]: row.get("error") for row in rows if row.get("status") == "FAILED"}
    if drill:
        failed[drill] = DRILL_ERROR
    not_attempted = sum(row.get("status") == "NOT_ATTEMPTED" for row in rows)
    _check(failed, population, not_attempted)
    write(quarantine_root / "original" / "collection-summary.json", summary)
    products = read(collection / "products.json")
    write(quarantine_root / "original" / "products.json", products)
    entries = []
    for sku in sorted(failed):
        path = collection / "pdp" / quote(sku, safe="") / "result.json"
        result = read(path) if path.is_file() else {}
        entry = _entry(sku, result, failed[sku])
        entry["drill"] = sku == drill
        entry["quarantined_capture"] = _move_capture(collection / "pdp", sku, quarantine_root / "pdp")
        entries.append(entry)
    kept = [row for row in rows if row["exact_sku"] not in failed]
    counts = dict(coverage.get("counts") or {})
    counts["FAILED"] = 0
    if "VERIFIED_EXACT_IDENTITY" in counts:
        counts["VERIFIED_EXACT_IDENTITY"] = sum(row.get("status") == "VERIFIED_EXACT_IDENTITY" for row in kept)
    coverage = {**coverage, "rows": kept, "counts": counts, "population_count": len(kept)}
    if isinstance(coverage.get("attempted_count"), int):
        coverage["attempted_count"] = len(kept)
    summary.update(coverage=coverage, status="PASS",
                   sku_quarantine={"contract": CONTRACT, "original_population_count": population,
                                   "allowance": allowance(population), "unverified": entries})
    write(collection / "products.json", [row for row in products if row.get("exact_sku") not in failed])
    write(collection / "collection-summary.json", summary)
    return entries


def quarantine_shards(collection, quarantine_root, statuses):
    """Quarantine failed rows across ``shard-*/shard-summary.json`` collections."""
    collection, quarantine_root = Path(collection), Path(quarantine_root)
    shards = sorted(path.parent for path in collection.glob("shard-*/shard-summary.json"))
    if not shards:
        raise QuarantineRefused("No shard summaries were written")
    summaries = {shard: read(shard / "shard-summary.json") for shard in shards}
    population = set(next(iter(summaries.values())).get("all_population_skus") or [])
    if any(set(item.get("all_population_skus") or []) != population for item in summaries.values()):
        raise QuarantineRefused("Shards disagree on the exact-SKU population")
    rows = {row["exact_sku"]: (shard, row) for shard, item in summaries.items() for row in item.get("rows", [])}
    failed = {sku: row.get("error") for sku, (_, row) in rows.items() if row.get("status") == "FAILED"}
    drill = None
    if all(item.get("status") == "PASS" for item in summaries.values()):
        drill = _drill_target([sku for sku, (_, row) in rows.items()
                               if row.get("status") == "VERIFIED_EXACT_IDENTITY"])
        if not drill:
            return []
        failed[drill] = DRILL_ERROR
    _check(failed, len(population), len(population - set(rows)))
    entries = []
    for sku in sorted(failed):
        shard, row = rows[sku]
        entry = _entry(sku, row, failed[sku])
        entry["drill"] = sku == drill
        entry["quarantined_capture"] = _move_capture(shard / "pdp", sku, quarantine_root / shard.name / "pdp")
        entries.append(entry)
    for shard, item in summaries.items():
        write(quarantine_root / "original" / shard.name / "shard-summary.json", item)
        products = read(shard / "products.json")
        write(quarantine_root / "original" / shard.name / "products.json", products)
        kept = [row for row in item.get("rows", []) if row["exact_sku"] not in failed]
        counts = {state: sum(row.get("status") == state for row in kept) for state in statuses}
        item.update(rows=kept, population_count=len(kept), coverage_counts=counts, status="PASS",
                    assigned_skus=sorted(row["exact_sku"] for row in kept),
                    all_population_skus=sorted(population - set(failed)),
                    sku_quarantine={"contract": CONTRACT, "original_population_count": len(population),
                                    "allowance": allowance(len(population)),
                                    "unverified": [entry for entry in entries if rows[entry["exact_sku"]][0] == shard]})
        write(shard / "products.json", [row for row in products if row.get("exact_sku") not in failed])
        write(shard / "shard-summary.json", item)
    return entries

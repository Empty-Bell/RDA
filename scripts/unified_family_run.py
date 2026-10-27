"""Run one family's existing acquisition and approved controls in one Actions run.

The entrypoint intentionally calls the established family scripts. It never
substitutes an earlier successful artifact or silently fills a failed source.
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from sku_quarantine import QuarantineRefused, quarantine_shards, quarantine_single


FAMILIES = (
    "refrigerator", "dishwasher", "washer", "tv", "range", "cooktop",
    "dryer", "hood", "monitor", "computer", "tablet",
)
GRADES = ("PASS", "HIGH", "MEDIUM", "LOW")
EPA_SIMPLE = ("range", "cooktop", "hood", "monitor")


def run(*args):
    command = [sys.executable, "scripts/" + args[0] + ".py", *map(str, args[1:])]
    print("RUN", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def run_collector(*args):
    """Run a collector whose FAILED exit still leaves a reviewable summary."""
    try:
        run(*args)
    except subprocess.CalledProcessError as error:
        print(f"COLLECTOR_EXIT {error.returncode}: {args[0]}", flush=True)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def single_summary(root, run_id):
    report = read(root / "collection-summary.json")
    if (report.get("status") != "PASS"
            or str(report.get("source_run_id")) != run_id
            or str(report.get("collection_run_id")) != run_id):
        raise ValueError("Exact-SKU collection did not pass")


def assess_refrigerator(root, source):
    family_source = root / "epa-family-current"
    run("g2_epa_family_current_capture", "--out", family_source)
    paths = (
        source / "report.json",
        source / "energy-star-source/epa-numeric/projection.json",
        source / "energy-star-source/three-point-input-review.json",
        source / "energy-star-source/energy-star-assessment.json",
    )
    archive = root / "g2-control-source.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in paths:
            if not path.is_file():
                raise ValueError(f"Missing G2 source control: {path}")
            output.write(path, "g2/" + path.name)
    run("g2_reassess_saved_bundle", "--source-zip", archive,
        "--family-source", family_source,
        "--out", root / "assessment")
    return root / "assessment/reassessment.json"


def source_and_collection(family, run_id, root):
    if family == "refrigerator":
        run("g2_smoke")
        sources = list(Path("runtime/g2").glob("*/checkpoint.json"))
        if len(sources) != 1:
            raise ValueError("Expected exactly one G2 source execution")
        checkpoint = read(sources[0])
        if checkpoint.get("status") != "PASS" or str(checkpoint.get("github_run_id")) != run_id:
            raise ValueError("Refrigerator full collection did not pass")
        # The accepted G2 refrigerator gate keeps its full-population identity rule.
        return sources[0].parent, []

    source_families = ("computer", "chromebook") if family == "computer" else (family,)
    for name in source_families:
        run("source_recon", "--family", name)
        recon = Path("runtime/source-recon") / name
        if not (recon / "recon.json").is_file() or not (recon / "fixtures").is_dir():
            raise ValueError(f"Source reconnaissance incomplete: {name}")
    source = Path("runtime/source-recon") / family
    collection = root / "collection"
    if family in {"computer", "tablet", "tv"}:
        shard_count = {"computer": 3, "tablet": 4, "tv": 8}[family]
        if family == "tv":
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(
                    run, "g3_tv_collect_shard", "--recon-root", source,
                    "--source-run-id", run_id, "--shard-index", index,
                    "--shard-count", shard_count,
                    "--out", collection / f"g3-tv-collection-shard-{index}",
                ) for index in range(shard_count)]
                for future in futures:
                    future.result()
            run_collector("g3_tv_aggregate_shards", "--recon-root", source,
                          "--source-run-id", run_id, "--shards-root", collection,
                          "--out", root / "combined")
            unverified = quarantine_single(root / "combined", root / "quarantine")
            single_summary(root / "combined", run_id)
            return root / "combined", unverified
        for index in range(shard_count):
            target = collection / f"shard-{index}"
            if family == "computer":
                run_collector("g3_computer_collect", "--computer-recon", source,
                    "--chromebook-recon", "runtime/source-recon/chromebook",
                    "--source-run-id", run_id, "--shard-index", index,
                    "--shard-count", shard_count, "--out", target)
            elif family == "tablet":
                run_collector("g3_tablet_collect", "--recon-root", source,
                    "--source-run-id", run_id, "--shard-index", index,
                    "--shard-count", shard_count, "--out", target)
        unverified = quarantine_shards(collection, root / "quarantine", (
            "VERIFIED_EXACT_IDENTITY", "PDP_REDIRECT_CONFIRMED", "FAILED"))
        summaries = [read(path) for path in sorted(collection.glob("shard-*/shard-summary.json"))]
        if len(summaries) != shard_count or any(item.get("status") != "PASS" for item in summaries):
            raise ValueError(f"Incomplete {family} exact-SKU shards")
        expected = set(summaries[0].get("all_population_skus", []))
        assigned = [sku for item in summaries for sku in item.get("assigned_skus", [])]
        if (not expected or len(assigned) != len(expected) or set(assigned) != expected
                or any(set(item.get("all_population_skus", [])) != expected for item in summaries)
                or any(str(item.get("source_run_id")) != run_id for item in summaries)):
            raise ValueError(f"{family} shard population or source identity differs")
        return collection, unverified

    run_collector("g3_" + family + "_collect", "--recon-root", source,
                  "--source-run-id", run_id, "--out", collection)
    unverified = quarantine_single(collection, root / "quarantine")
    single_summary(collection, run_id)
    return collection, unverified


def assess_epa(family, run_id, root, collection):
    if family in EPA_SIMPLE:
        run(f"g3_{family}_epa_capture", "--out", root / "epa")
        candidates = root / "epa-source-candidates"
        run(f"g3_{family}_epa_candidates", "--collection-root", collection,
            "--collection-run-id", run_id, "--epa-root", root / "epa",
            "--epa-run-id", run_id, "--out", candidates)
        run(f"g3_{family}_energy_star_assessment", "--candidates",
            candidates / f"{family}-epa-source-candidates.json", "--out", root / "assessment")
        return root / "assessment/energy-star-assessment.json"
    if family == "dryer":
        run("g3_dryer_epa_capture", "--out", root / "epa")
        run("g3_dryer_combo_epa_capture", "--out", root / "epa-combo")
        candidates = root / "epa-claim-candidates"
        run("g3_dryer_epa_claim_candidates", "--collection-root", collection,
            "--collection-run-id", run_id, "--epa-root", root / "epa",
            "--epa-run-id", run_id, "--combo-epa-root", root / "epa-combo",
            "--combo-epa-run-id", run_id, "--out", candidates)
        run("g3_dryer_energy_star_assessment", "--candidates",
            candidates / "epa-claim-candidates.json", "--out", root / "assessment")
        return root / "assessment/energy-star-assessment.json"
    if family in {"computer", "tablet"}:
        run(f"g3_{family}_epa_candidates", "--collection-root", collection,
            "--collection-run-id", run_id, "--out", root / "epa-candidates")
        path = root / "epa-candidates/candidates" / f"{family}-epa-source-candidates.json"
        if family == "computer":
            run("g3_computer_energy_star_assessment", "--candidates", path,
                "--out", root / "assessment")
            return root / "assessment/energy-star-assessment.json"
        run("g3_tablet_assessment", "--candidates", path,
            "--epa-root", root / "epa-candidates/epa-current-source", "--out", root / "assessment")
        return root / "assessment/assessment.json"
    raise ValueError(f"Unsupported EPA family: {family}")


def assess_washer_or_tv(family, run_id, root, collection):
    prefix = "g3_" + family + "_"
    run(prefix + "epa_capture", "--out", root / "epa")
    run(prefix + "energyguide_collect", "--collection-root", collection,
        "--collection-run-id", run_id, "--out", root / "energyguide")
    run(prefix + "energyguide_observe", "--retrieval-root", root / "energyguide",
        "--retrieval-run-id", run_id, "--out", root / "observation")
    run(prefix + "energyguide_review_queue", "--observation-root", root / "observation",
        "--observation-run-id", run_id, "--out", root / "review")
    run(prefix + "source_comparison", "--review-root", root / "review",
        "--collection-root", collection, "--collection-run-id", run_id,
        "--epa-root", root / "epa", "--epa-run-id", run_id,
        "--out", root / "comparison")
    comparison = root / "comparison/source-comparison-candidates.json"
    run(prefix + "assessment", "--comparison", comparison,
        "--collection-root", collection, "--out", root / "assessment")
    return root / "assessment/assessment.json"


def assess_dishwasher(run_id, root, collection):
    run("g3_dishwasher_epa_capture", "--out", root / "epa")
    run("g3_dishwasher_energyguide_collect", "--collection-root", collection,
        "--collection-run-id", run_id, "--out", root / "energyguide")
    run("g3_dishwasher_energyguide_observe", "--retrieval-root", root / "energyguide",
        "--retrieval-run-id", run_id, "--out", root / "observation")
    run("g3_dishwasher_source_match", "--observation-root", root / "observation",
        "--epa-root", root / "epa", "--pdp-root", collection, "--out", root / "match")
    run("g3_dishwasher_comparison_package", "--pdp-root", collection,
        "--observation-root", root / "observation", "--epa-root", root / "epa",
        "--match-root", root / "match",
        "--model-review", "docs/evidence/g3-dishwasher-energyguide-visual-review.json",
        "--out", root / "package")
    package = root / "package/comparison-package.json"
    run("g3_dishwasher_numeric_comparison", "--package", package, "--out", root / "numeric")
    run("g3_dishwasher_model_comparison", "--package", package, "--out", root / "model")
    run("g3_dishwasher_energy_star_assessment", "--collection-root", collection,
        "--match", root / "match/match-report.json", "--out", root / "energy-star")
    run("g3_dishwasher_assessment", "--energy-star", root / "energy-star/energy-star-assessment.json",
        "--numeric", root / "numeric/numeric-comparison.json",
        "--model", root / "model/model-comparison.json", "--out", root / "assessment")
    readiness = read(root / "assessment/readiness.json")
    if readiness.get("status") != "READY_FOR_ASSESSMENT":
        raise ValueError("Dishwasher formal readiness is blocked")
    return root / "assessment/assessment.json"


def failure_digest(family, root):
    """Print every unresolved exact-SKU failure so logs alone explain a stop."""
    lines, seen = [], set()
    for path in sorted(Path(root).rglob("result.json")):
        if any(part.startswith(("retry", "initial-attempt")) for part in path.parts):
            continue
        try:
            row = read(path)
        except (OSError, ValueError):
            continue
        sku = row.get("exact_sku")
        if row.get("status") != "FAILED" or not sku or sku in seen:
            continue
        seen.add(sku)
        listing = row.get("source_claim_listing_raw") or {}
        lines.append(f"{sku} | {row.get('error')} | {row.get('requested_url')} -> {row.get('final_url')}"
                     f" | stockFlag={listing.get('stockFlag') if isinstance(listing, dict) else None}")
    for line in lines[:20]:
        print(f"::error title=RDA {family} source failure::{line}", flush=True)
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary and lines:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write(f"### {family} unresolved exact-SKU failures\n\n")
            stream.writelines(f"- `{line}`\n" for line in lines)


def collect_phase(family, run_id, root):
    try:
        collection, unverified = source_and_collection(family, run_id, root)
    except Exception as error:
        failure_digest(family, root)
        if isinstance(error, QuarantineRefused):
            print(f"::error title=RDA {family} quarantine refused::{error}", flush=True)
        raise
    for entry in unverified:
        print(f"::warning title=RDA {family} unverified SKU::{entry['exact_sku']} | {entry.get('error')}"
              f" | {entry.get('requested_url')} -> {entry.get('final_url')}", flush=True)
    state = {"family": family, "run_id": run_id, "collection": str(collection), "unverified": unverified}
    (root / "collection-state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(family, out, phase="all"):
    if family not in FAMILIES:
        raise ValueError(f"Unknown family: {family}")
    run_id = os.getenv("GITHUB_RUN_ID", "").strip()
    if not run_id.isdigit():
        raise ValueError("This entrypoint requires a hosted GitHub Actions run ID")
    root = Path(out) / family
    root.mkdir(parents=True, exist_ok=True)
    if phase in {"all", "collect"}:
        collect_phase(family, run_id, root)
    if phase == "collect":
        return
    state = read(root / "collection-state.json")
    if state.get("family") != family or str(state.get("run_id")) != run_id:
        raise ValueError(f"{family} collection state belongs to another run")
    collection, unverified = Path(state["collection"]), state["unverified"]
    if family == "refrigerator":
        assessment = assess_refrigerator(root, collection)
    elif family in {"washer", "tv"}:
        assessment = assess_washer_or_tv(family, run_id, root, collection)
    elif family == "dishwasher":
        assessment = assess_dishwasher(run_id, root, collection)
    else:
        assessment = assess_epa(family, run_id, root, collection)
    result = read(assessment)
    rows = result.get("records", result.get("rows"))
    if (result.get("status") != "PASS" or result.get("readiness_gaps")
            or not isinstance(rows, list) or not rows or len(rows) != result.get("sku_count")):
        raise ValueError(f"{family} assessment is incomplete")
    skus = [row.get("exact_sku") for row in rows]
    grades = [row.get("grade", row.get("display_outcome")) for row in rows]
    if (len(set(skus)) != len(skus) or any(not sku for sku in skus)
            or any(grade not in GRADES for grade in grades)):
        raise ValueError(f"{family} has duplicate or unclassified models")
    if {entry["exact_sku"] for entry in unverified} & set(skus):
        raise ValueError(f"{family} graded an exact SKU that was quarantined as unverified")
    counts = Counter(grades)
    reported = result.get("counts") or {}
    if any(reported.get(level, 0) != counts[level] for level in GRADES):
        raise ValueError(f"{family} grade totals differ from model rows")
    manifest = {"contract": "RDA_UNIFIED_FAMILY_EXECUTION_V1", "family": family,
                "run_id": run_id, "git_sha": os.getenv("GITHUB_SHA"),
                "assessment_path": str(assessment),
                "assessment_sha256": hashlib.sha256(assessment.read_bytes()).hexdigest(),
                "assessment_contract": result.get("contract"),
                "assessment_status": result.get("status"),
                "source_run_ids": result.get("source_run_ids"),
                "sku_count": result.get("sku_count"),
                "counts": {level: counts[level] for level in GRADES},
                "unverified": unverified}
    (root / "unified-family-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=FAMILIES, required=True)
    parser.add_argument("--out", default="runtime/unified")
    parser.add_argument("--phase", choices=("all", "collect", "assess"), default="all")
    args = parser.parse_args()
    main(args.family, args.out, args.phase)

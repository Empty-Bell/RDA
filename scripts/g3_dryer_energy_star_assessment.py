"""Assess Dryer ENERGY STAR registration and three-point publication consistency."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path

try:
    from .epa_only_rules import epa_registration_state, publication_assessment, publication_points
except ImportError:  # direct `python scripts/...py` execution on Actions
    from epa_only_rules import epa_registration_state, publication_assessment, publication_points


CONTRACT = "G3_DRYER_ENERGY_STAR_ASSESSMENT_V1"


def build(candidate_path, output):
    source = json.loads(Path(candidate_path).read_bytes())
    rows = source.get("rows")
    if (source.get("contract") != "G3_DRYER_EPA_CLAIM_CANDIDATES_V1"
            or source.get("status") != "SOURCE_CANDIDATES_READY"
            or source.get("source_validation") != "PASS"
            or not isinstance(rows, list)
            or not rows
            or len(rows) != source.get("population_count")):
        raise ValueError("Dryer EPA candidates are not a complete validated source artifact")
    skus = [row.get("exact_sku") for row in rows]
    if not all(isinstance(sku, str) and sku for sku in skus) or len(set(skus)) != len(skus):
        raise ValueError("Dryer EPA candidates contain missing or duplicate exact SKUs")

    records = []
    findings = []
    for row in sorted(rows, key=lambda item: item["exact_sku"]):
        claim = row.get("energy_star_claim_sources_raw")
        if not isinstance(claim, dict) or claim.get("exact_sku") != row["exact_sku"]:
            raise ValueError("Dryer publication evidence lacks exact-SKU provenance")
        dryer = row.get("dryer_epa_model_pattern_candidates")
        combo = row.get("combo_epa_model_pattern_candidates")
        if not isinstance(dryer, list) or not isinstance(combo, list):
            raise ValueError("EPA model candidate arrays are missing")
        registration, market_states = epa_registration_state(dryer, combo)
        points = publication_points(claim)
        outcome, row_findings = publication_assessment(registration, points)
        record = {
            "exact_sku": row["exact_sku"],
            "epa_current_registration": {
                "state": registration,
                "dryer_model_candidates": dryer,
                "combo_model_candidates": combo,
                "candidate_market_states": market_states,
            },
            "energy_star_publication": {"outcome": outcome, "points": points},
            "display_outcome": "PASS" if outcome == "NO_FINDING" else outcome,
            "findings": row_findings,
            "overall_product_compliance": "NOT_EVALUATED",
        }
        records.append(record)
        findings.extend({"exact_sku": row["exact_sku"], **finding} for finding in row_findings)

    counts = Counter(record["display_outcome"] for record in records)
    report = {
        "contract": CONTRACT,
        "status": "PASS",
        "assessment_enabled": True,
        "source_candidate_run_ids": {
            "collection": source.get("collection_run_id"),
            "epa_capture": source.get("epa_capture_run_id"),
            "combo_epa_capture": source.get("combo_epa_capture_run_id"),
        },
        "assessment_run_id": os.getenv("GITHUB_RUN_ID"),
        "git_sha": source.get("git_sha"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sku_count": len(records),
        "finding_count": len(findings),
        "affected_sku_count": len({finding["exact_sku"] for finding in findings}),
        "counts": {level: counts.get(level, 0) for level in
                   ("HIGH", "MEDIUM", "LOW", "PASS", "NOT_EVALUATED")},
        "rules": {
            "epa_us_registered_and_all_three_points_present": "PASS",
            "epa_us_registered_and_any_point_absent": "LOW",
            "epa_us_unregistered_and_any_point_present": "HIGH",
            "epa_us_unregistered_and_all_points_absent": "PASS_NO_FINDING",
            "unknown_epa_or_publication_evidence": "NOT_EVALUATED",
            "overall_product_compliance": "NOT_EVALUATED",
        },
        "findings": findings,
        "records": records,
        "overall_product_compliance": "NOT_EVALUATED",
    }
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "energy-star-assessment.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Dryer ENERGY STAR publication assessment\n\n")
            stream.write(f"Exact SKUs: **{len(records)}** | HIGH: **{report['counts']['HIGH']}** | LOW: **{report['counts']['LOW']}** | PASS: **{report['counts']['PASS']}** | NOT EVALUATED: **{report['counts']['NOT_EVALUATED']}**\n\n")
            stream.write("This assesses only current EPA US model registration and PLP, PDP logo, and PDP Specs publication consistency. It is not a legal compliance conclusion.\n")
    print(json.dumps({"status": "PASS", "counts": report["counts"],
                      "finding_count": report["finding_count"]}, sort_keys=True))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build(args.candidates, args.out)


if __name__ == "__main__":
    main()

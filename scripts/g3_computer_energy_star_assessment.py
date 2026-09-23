"""Assess Computer ENERGY STAR registration and publication consistency."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from epa_only_rules import epa_registration_state, publication_assessment, publication_points

SOURCE_CONTRACT = "G3_COMPUTER_EPA_SOURCE_CANDIDATES_V1"
CONTRACT = "G3_COMPUTER_ENERGY_STAR_ASSESSMENT_V1"
EXPECTED_POPULATION = 24


def computer_registration(candidates):
    """Only Notebook rows can establish this computer family's registration."""
    if not candidates:
        return "ABSENT", []
    if any(not isinstance(item, dict) for item in candidates):
        return "UNKNOWN", []
    if any(str((item.get("epa_row_raw") or {}).get("type_raw") or "").strip().casefold() != "notebook"
           for item in candidates):
        return "UNKNOWN", ["UNKNOWN" for _ in candidates]
    projected = [{"markets_raw": (item.get("epa_row_raw") or {}).get("markets_raw")}
                 for item in candidates]
    return epa_registration_state(projected, [])


def assess_record(row):
    sku = row.get("exact_sku")
    claim = row.get("energy_star_claim_sources_raw")
    candidates = row.get("epa_computer_model_pattern_candidates")
    if not isinstance(sku, str) or not sku or not isinstance(claim, dict) or claim.get("exact_sku") != sku:
        raise ValueError("Computer publication evidence lacks exact-SKU provenance")
    if not isinstance(candidates, list):
        raise ValueError("Computer EPA candidate list is missing")
    registration, market_states = computer_registration(candidates)
    points = publication_points(claim)
    outcome, findings = publication_assessment(registration, points)
    return {
        "exact_sku": sku,
        "selected_configuration_raw": row.get("selected_configuration_raw"),
        "pdp_product_facts_raw": row.get("pdp_product_facts_raw", {}),
        "epa_current_registration": {
            "state": registration,
            "computer_model_pattern_candidates": candidates,
            "candidate_market_states": market_states,
        },
        "energy_star_publication": {"outcome": outcome, "points": points},
        "display_outcome": "PASS" if outcome == "NO_FINDING" else outcome,
        "findings": findings,
        "overall_product_compliance": "NOT_EVALUATED",
        "legal_applicability": "NOT_EVALUATED",
    }


def build(candidate_path, output):
    source = json.loads(Path(candidate_path).read_bytes())
    rows = source.get("records")
    if (source.get("contract") != SOURCE_CONTRACT
            or source.get("status") != "SOURCE_CANDIDATES_READY"
            or source.get("source_validation") != "PASS"
            or not isinstance(rows, list)
            or len(rows) != EXPECTED_POPULATION
            or len(rows) != source.get("population_count")):
        raise ValueError("Computer source candidates are not a complete validated 24-SKU artifact")
    skus = [row.get("exact_sku") for row in rows]
    if not all(isinstance(sku, str) and sku for sku in skus) or len(set(skus)) != len(skus):
        raise ValueError("Computer source candidates contain missing or duplicate exact SKUs")

    records = [assess_record(row) for row in sorted(rows, key=lambda item: item["exact_sku"])]
    findings = [{"exact_sku": record["exact_sku"], **finding}
                for record in records for finding in record["findings"]]
    counts = Counter(record["display_outcome"] for record in records)
    registration_counts = Counter(record["epa_current_registration"]["state"] for record in records)
    point_counts = {
        point: Counter(record["energy_star_publication"]["points"][point]["state"] for record in records)
        for point in ("plp_logo", "pdp_logo", "spec_certification")
    }
    report = {
        "contract": CONTRACT,
        "status": "PASS",
        "assessment_enabled": True,
        "assessment_run_id": os.getenv("GITHUB_RUN_ID"),
        "source_run_ids": {
            "collection": source.get("collection_run_id"),
            "epa_capture": source.get("epa_capture_run_id"),
        },
        "git_sha": source.get("git_sha"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sku_count": len(records),
        "finding_count": len(findings),
        "affected_sku_count": len({finding["exact_sku"] for finding in findings}),
        "counts": {level: counts.get(level, 0)
                   for level in ("HIGH", "MEDIUM", "LOW", "PASS", "NOT_EVALUATED")},
        "diagnostics": {
            "epa_us_registration_states": dict(registration_counts),
            "publication_point_states": {key: dict(value) for key, value in point_counts.items()},
        },
        "rules": {
            "epa_current_us_notebook_and_all_three_points_present": "PASS",
            "epa_current_us_notebook_and_any_point_absent": "LOW",
            "no_matching_us_epa_notebook_and_any_point_present": "HIGH",
            "no_matching_us_epa_notebook_and_all_points_absent": "PASS_NO_FINDING",
            "unknown_type_market_or_publication_evidence": "NOT_EVALUATED",
            "overall_product_compliance": "NOT_EVALUATED",
            "legal_applicability": "NOT_EVALUATED",
        },
        "findings": findings,
        "records": records,
        "overall_product_compliance": "NOT_EVALUATED",
        "legal_applicability": "NOT_EVALUATED",
    }
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "energy-star-assessment.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("## Computer ENERGY STAR publication assessment\n\n")
            stream.write(f"Exact SKUs: **{len(records)}** | HIGH: **{report['counts']['HIGH']}** | LOW: **{report['counts']['LOW']}** | PASS: **{report['counts']['PASS']}** | NOT EVALUATED: **{report['counts']['NOT_EVALUATED']}**\n\n")
            stream.write("This checks only current U.S. EPA Notebook registration and PLP logo, PDP logo, and Specs certification publication.\n\n")
            stream.write("| Exact SKU | EPA U.S. state | PLP | PDP logo | Specs | Result |\n|---|---|---|---|---|---|\n")
            for record in records:
                points = record["energy_star_publication"]["points"]
                states = [points[key]["state"] for key in ("plp_logo", "pdp_logo", "spec_certification")]
                stream.write(f"| {record['exact_sku']} | {record['epa_current_registration']['state']} | {states[0]} | {states[1]} | {states[2]} | {record['display_outcome']} |\n")
    print(json.dumps({"status": report["status"], "sku_count": len(records),
                      "counts": report["counts"], "diagnostics": report["diagnostics"],
                      "finding_count": report["finding_count"], "findings": findings},
                     ensure_ascii=False, sort_keys=True), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build(args.candidates, args.out)


if __name__ == "__main__":
    main()

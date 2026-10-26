"""Assess only Monitor EPA registration and ENERGY STAR publication consistency."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from epa_only_rules import epa_registration_state, publication_assessment, publication_points

SOURCE_CONTRACT = "G3_MONITOR_EPA_SOURCE_CANDIDATES_V1"
CONTRACT = "G3_MONITOR_ENERGY_STAR_ASSESSMENT_V1"
VALID_MATCH_RULES = {"LITERAL_PDP_SKU", "PDP_SKU_WITH_SINGLE_LEADING_L_OMITTED"}


def assess_record(row):
    sku = row.get("exact_sku")
    claim = row.get("energy_star_claim_sources_raw")
    all_candidates = row.get("epa_display_pattern_candidates")
    if not isinstance(sku, str) or not sku or not isinstance(claim, dict) or claim.get("exact_sku") != sku:
        raise ValueError("Monitor claim evidence lacks exact-SKU provenance")
    if not isinstance(all_candidates, list):
        raise ValueError("Monitor EPA candidate list is missing")
    monitor_candidates = []
    for candidate in all_candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Monitor EPA candidate is malformed")
        if str(candidate.get("display_type_raw") or "").strip().casefold() != "monitor":
            continue
        if candidate.get("match_rule") not in VALID_MATCH_RULES:
            raise ValueError("Monitor candidate has an unapproved or undocumented match rule")
        monitor_candidates.append(candidate)
    registration, market_states = epa_registration_state(monitor_candidates, [])
    points = publication_points(claim)
    points["spec_certification"] = {
        "state": "NOT_APPLICABLE",
        "inspection": "MONITOR_FAMILY_SPECS_HAS_NO_ENERGY_STAR_CERTIFICATION_FIELD",
        "visible_rows_raw": [],
    }
    applicable_points = {key: value for key, value in points.items()
                         if value["state"] != "NOT_APPLICABLE"}
    outcome, findings = publication_assessment(registration, applicable_points)
    return {
        "exact_sku": sku,
        "pdp_product_facts_raw": row.get("pdp_product_facts_raw", {}),
        "epa_current_registration": {
            "state": registration,
            "monitor_model_pattern_candidates": monitor_candidates,
            "candidate_market_states": market_states,
        },
        "energy_star_publication": {"outcome": outcome, "points": points},
        "display_outcome": "PASS" if outcome == "NO_FINDING" else outcome,
        "findings": findings,
        "overall_product_compliance": "NOT_EVALUATED",
        "legal_applicability": "NOT_EVALUATED",
    }


def build(candidates_path, output):
    source = json.loads(Path(candidates_path).read_bytes())
    rows = source.get("records")
    if (source.get("contract") != SOURCE_CONTRACT
            or source.get("status") != "SOURCE_CANDIDATES_READY"
            or source.get("source_validation") != "PASS"
            or not isinstance(rows, list) or not rows
            or len(rows) != source.get("population_count")):
        raise ValueError("Monitor source candidate artifact is incomplete or invalid")
    if "single initial L may be omitted" not in source.get("model_candidate_contract", ""):
        raise ValueError("Monitor source artifact does not declare the approved leading-L rule")
    skus = [row.get("exact_sku") for row in rows]
    if not all(isinstance(sku, str) and sku for sku in skus) or len(set(skus)) != len(skus):
        raise ValueError("Monitor candidates contain missing or duplicate exact SKUs")
    records = [assess_record(row) for row in sorted(rows, key=lambda item: item["exact_sku"])]
    findings = [{"exact_sku": record["exact_sku"], **finding}
                for record in records for finding in record["findings"]]
    outcomes = Counter(record["display_outcome"] for record in records)
    registrations = Counter(record["epa_current_registration"]["state"] for record in records)
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
            "candidates": os.getenv("CANDIDATE_RUN_ID"),
        },
        "git_sha": os.getenv("GITHUB_SHA"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sku_count": len(records),
        "finding_count": len(findings),
        "affected_sku_count": len({finding["exact_sku"] for finding in findings}),
        "counts": {level: outcomes.get(level, 0)
                   for level in ("HIGH", "MEDIUM", "LOW", "PASS", "NOT_EVALUATED")},
        "diagnostics": {
            "epa_us_registration_states": dict(registrations),
            "publication_point_states": {key: dict(value) for key, value in point_counts.items()},
        },
        "rules": {
            "epa_us_registered_and_all_applicable_publication_points_present": "PASS",
            "epa_us_registered_and_any_applicable_point_absent": "LOW",
            "epa_us_unregistered_and_any_point_present": "HIGH",
            "epa_us_unregistered_and_all_points_absent": "PASS_NO_FINDING",
            "incomplete_or_unknown_evidence": "NOT_EVALUATED",
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
            stream.write("## Monitor ENERGY STAR publication consistency\n\n")
            stream.write(f"Exact SKUs: **{len(records)}** | HIGH: **{report['counts']['HIGH']}** | LOW: **{report['counts']['LOW']}** | PASS: **{report['counts']['PASS']}** | NOT EVALUATED: **{report['counts']['NOT_EVALUATED']}**\n\n")
            stream.write("Only US Monitor rows and the approved model match are assessed. Specs certification is NOT_APPLICABLE because the complete Monitor Specs arrays have no ENERGY STAR certification field. Legal applicability and overall product compliance remain NOT_EVALUATED.\n\n")
            if findings:
                stream.write("| Exact SKU | Severity | Issue |\n|---|---|---|\n")
                for finding in findings:
                    stream.write(f"| {finding['exact_sku']} | {finding['severity']} | {finding['issue_code']} |\n")
    print(json.dumps({
        "status": report["status"], "counts": report["counts"],
        "epa_us_registration_states": report["diagnostics"]["epa_us_registration_states"],
        "publication_point_states": report["diagnostics"]["publication_point_states"],
        "finding_count": report["finding_count"], "findings": findings,
        "low_skus": [record["exact_sku"] for record in records if record["display_outcome"] == "LOW"],
        "overall_product_compliance": "NOT_EVALUATED",
        "legal_applicability": "NOT_EVALUATED",
    }, ensure_ascii=False, sort_keys=True), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build(args.candidates, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

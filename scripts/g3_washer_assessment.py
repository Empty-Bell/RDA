"""Apply approved Washer Energy Star publication and annual-energy severity rules."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path


CONTRACT = "G3_WASHER_ASSESSMENT_V1"
RANK = {"PASS": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
TRUE_VALUES = {"yes", "y", "true", "1"}
FALSE_VALUES = {"no", "n", "false", "0"}


def read_json(path):
    return json.loads(Path(path).read_bytes())


def flag_point(raw):
    value = str(raw).strip().lower() if raw is not None else ""
    state = "PRESENT" if value in TRUE_VALUES else "ABSENT" if value in FALSE_VALUES else "UNKNOWN"
    return {"state": state, "raw_value": raw}


def pdp_logo_point(claim):
    flags = [row.get("value") for row in claim.get("pdp_nested_energy_star_fields_raw", [])
             if row.get("name") == "energyStarFlag"]
    flags = list(dict.fromkeys(flags))
    badges = claim.get("rendered_attributed_badges_raw", [])
    states = [flag_point(value)["state"] for value in flags]
    if badges or "PRESENT" in states:
        state = "PRESENT"
    elif states and set(states) == {"ABSENT"}:
        state = "ABSENT"
    else:
        state = "UNKNOWN"
    return {"state": state, "raw_flag_values": flags, "attributed_badges_raw": badges}


def spec_point(rows):
    selected = [row for row in rows or []
                if "energy star" in str(row.get("name", "")).lower()
                and "certif" in str(row.get("name", "")).lower()]
    if not selected:
        return {"state": "ABSENT", "raw_rows": []}
    values = {str(row.get("value", "")).strip().lower() for row in selected}
    if values and values <= TRUE_VALUES:
        state = "PRESENT"
    elif values and values <= FALSE_VALUES:
        state = "ABSENT"
    else:
        state = "UNKNOWN"
    return {"state": state, "raw_rows": selected}


def publication_assessment(epa_registered, points):
    states = [point["state"] for point in points.values()]
    if epa_registered and all(state == "PRESENT" for state in states):
        return "PASS", []
    if epa_registered and "ABSENT" in states:
        return "LOW", [{"control": "ENERGY_STAR_PUBLICATION", "severity": "LOW",
                        "issue_code": "ENERGY_STAR_PUBLICATION_INCONSISTENT"}]
    if not epa_registered and "PRESENT" in states:
        return "HIGH", [{"control": "ENERGY_STAR_PUBLICATION", "severity": "HIGH",
                         "issue_code": "ENERGY_STAR_CLAIM_WITHOUT_CURRENT_EPA_REGISTRATION"}]
    if not epa_registered and all(state == "ABSENT" for state in states):
        return "PASS", []
    return "NOT_EVALUATED", []


def build(comparison_path, collection_root, out):
    comparison = read_json(comparison_path)
    if comparison.get("status") != "PASS" or comparison.get("contract") != "G3_WASHER_SOURCE_COMPARISON_CANDIDATES_V1":
        raise ValueError("Washer source comparison is not a successful supported artifact")
    root = Path(collection_root)
    collection = read_json(root / "collection-summary.json")
    if (collection.get("status") != "PASS"
            or str(collection.get("collection_run_id")) != str(comparison.get("collection_run_id"))):
        raise ValueError("Washer collection and comparison run IDs differ")
    results = [read_json(path) for path in sorted(root.glob("pdp/*/result.json"))]
    result_by_sku = {row.get("exact_sku"): row for row in results}
    rows = comparison.get("rows", [])
    if (len(result_by_sku) != comparison.get("population_count")
            or set(result_by_sku) != {row.get("exact_sku") for row in rows}):
        raise ValueError("Washer assessment source populations differ")

    records, all_findings = [], []
    for source in sorted(rows, key=lambda row: row["exact_sku"]):
        sku = source["exact_sku"]
        claim = result_by_sku[sku].get("energy_star_claim_sources_raw") or {}
        publication_points = {
            "plp_logo": flag_point(claim.get("plp_energy_star_flag_raw")),
            "pdp_logo": pdp_logo_point(claim),
            "spec_certification": spec_point(claim.get("pdp_spec_energy_star_claim_raw")),
        }
        epa_registered = bool(source.get("epa_current_model_matches"))
        publication_outcome, findings = publication_assessment(epa_registered, publication_points)

        energy_state = source.get("energy_comparison_candidate")
        values = source.get("source_kwh_values", {})
        if energy_state == "SOURCE_VALUES_DIFFER":
            findings.append({"control": "ANNUAL_ENERGY", "severity": "MEDIUM",
                             "issue_code": "ANNUAL_ENERGY_MISMATCH"})
        if not values.get("PDP") and values.get("LABEL") and values.get("EPA_US_MARKET_CANDIDATE"):
            findings.append({"control": "ANNUAL_ENERGY", "severity": "LOW",
                             "issue_code": "PDP_ANNUAL_ENERGY_MISSING"})
        findings = sorted({(finding["control"], finding["severity"], finding["issue_code"]): finding
                           for finding in findings}.values(),
                          key=lambda finding: (finding["control"], finding["issue_code"]))
        display_outcome = max((finding["severity"] for finding in findings),
                              key=RANK.__getitem__, default="PASS")
        record = {
            "exact_sku": sku,
            "display_outcome": display_outcome,
            "epa_current_registration": {
                "state": "PRESENT" if epa_registered else "ABSENT",
                "matched_models_raw": [row.get("model_number_raw") for row in source.get("epa_current_model_matches", [])],
            },
            "energy_star_publication": {"outcome": publication_outcome, "points": publication_points},
            "annual_energy": {"comparison_candidate": energy_state, "source_kwh_values": values},
            "findings": findings,
            "overall_product_compliance": "NOT_EVALUATED",
        }
        records.append(record)
        all_findings.extend({"exact_sku": sku, **finding} for finding in findings)

    counts = Counter(record["display_outcome"] for record in records)
    report = {
        "contract": CONTRACT,
        "status": "PASS",
        "assessment_enabled": True,
        "comparison_run_id": comparison.get("comparison_run_id"),
        "collection_run_id": comparison.get("collection_run_id"),
        "assessment_run_id": os.getenv("GITHUB_RUN_ID"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sku_count": len(records),
        "finding_count": len(all_findings),
        "affected_sku_count": len({finding["exact_sku"] for finding in all_findings}),
        "counts": {level: counts.get(level, 0) for level in ("HIGH", "MEDIUM", "LOW", "PASS")},
        "rules": {
            "energy_star_registered_all_three_points_present": "PASS",
            "energy_star_registered_any_point_absent": "LOW",
            "energy_star_not_registered_any_point_present": "HIGH",
            "energy_star_not_registered_all_points_absent": "PASS",
            "annual_energy_source_values_differ": "MEDIUM",
            "pdp_annual_energy_missing_while_label_and_epa_agree": "LOW",
            "sku_display_outcome": "HIGHEST_FINDING_SEVERITY; NO_FINDING_COUNTS_AS_PASS",
        },
        "findings": all_findings,
        "records": records,
        "overall_product_compliance": "NOT_EVALUATED",
    }
    destination = Path(out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "assessment.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = ["# G3 Washer assessment", "",
             f"SKUs: **{len(records)}** | HIGH: **{report['counts']['HIGH']}** | MEDIUM: **{report['counts']['MEDIUM']}** | LOW: **{report['counts']['LOW']}** | PASS: **{report['counts']['PASS']}**",
             "", "| Exact SKU | Result | EPA current | PLP logo | PDP logo | Spec certification | Annual kWh | Findings |",
             "|---|---|---|---|---|---|---|---|"]
    for record in records:
        points = record["energy_star_publication"]["points"]
        findings = ", ".join(finding["issue_code"] for finding in record["findings"]) or "—"
        lines.append(f"| {record['exact_sku']} | {record['display_outcome']} | {record['epa_current_registration']['state']} | "
                     f"{points['plp_logo']['state']} | {points['pdp_logo']['state']} | {points['spec_certification']['state']} | "
                     f"{record['annual_energy']['comparison_candidate']} | {findings} |")
    markdown = "\n".join(lines) + "\n"
    (destination / "assessment.md").write_text(markdown, encoding="utf-8")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).write_text(markdown, encoding="utf-8")
    print(json.dumps({"status": "PASS", "sku_count": len(records), "finding_count": len(all_findings),
                      "counts": report["counts"], "records": records}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", required=True)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    return build(args.comparison, args.collection_root, args.out)


if __name__ == "__main__":
    raise SystemExit(main())

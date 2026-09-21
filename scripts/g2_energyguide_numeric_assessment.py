"""Apply the approved refrigerator PDP/EnergyGuide numeric finding rules."""

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any


CONTRACT = "G2_ENERGYGUIDE_NUMERIC_ASSESSMENT_V1"
COMPARISON_CONTRACT = "G2_ENERGYGUIDE_PDP_NUMERIC_COMPARISON_OBSERVATION_V1"
ANNUAL_MISSING_ISSUE = "PDP_ANNUAL_ENERGY_MISSING"
CAPACITY_MISMATCH_ISSUE = "PDP_ENERGYGUIDE_CAPACITY_MISMATCH"
SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2}


def _finding(issue_code: str, severity: str, field: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "issue_code": issue_code,
        "severity": severity,
        "field": field,
        "evidence": {
            key: evidence.get(key) for key in (
                "state", "reason", "pdp_amount", "label_amount", "epa_amount",
                "epa_state", "label_epa_relation", "pdp_epa_relation",
                "delta_pdp_minus_label",
            )
        },
    }


def build_assessment(comparison: dict[str, Any]) -> dict[str, Any]:
    if (comparison.get("contract") != COMPARISON_CONTRACT
            or comparison.get("status") != "PASS"
            or comparison.get("assessment_enabled") is not False):
        raise ValueError("Numeric comparison observation contract is invalid")
    if comparison.get("scope", {}).get("comparison_mode") != "OBSERVATION_ONLY_NO_TOLERANCE_NO_FINDINGS":
        raise ValueError("Numeric comparison mode is unsupported")
    records = comparison.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Numeric comparison records are unavailable")
    skus = [record.get("exact_sku") for record in records if isinstance(record, dict)]
    if len(skus) != len(records) or any(not isinstance(sku, str) or not sku for sku in skus):
        raise ValueError("Numeric comparison exact SKU is invalid")
    if len(set(skus)) != len(skus):
        raise ValueError("Numeric comparison exact SKU is duplicated")

    output = []
    for record in sorted(records, key=lambda item: item["exact_sku"]):
        annual = record.get("annual_energy_kwh")
        capacity = record.get("capacity_cu_ft")
        if not isinstance(annual, dict) or not isinstance(capacity, dict):
            raise ValueError("Numeric comparison measurement is invalid")
        findings = []
        if annual.get("state") == "NOT_COMPARABLE" and annual.get("reason") == "PDP_VALUE_MISSING":
            findings.append(_finding(ANNUAL_MISSING_ISSUE, "LOW", "annual_energy_kwh", annual))
        elif annual.get("state") not in {"EQUAL", "NOT_COMPARABLE"}:
            # Numeric annual-energy conflicts have no approved rule yet.
            display_outcome = "NOT_EVALUATED"
        else:
            display_outcome = "PASS"

        if capacity.get("state") == "DIFFERENT":
            findings.append(_finding(CAPACITY_MISMATCH_ISSUE, "MEDIUM", "capacity_cu_ft", capacity))
        elif capacity.get("state") not in {"EQUAL", "NOT_COMPARABLE"}:
            display_outcome = "NOT_EVALUATED"

        if findings:
            display_outcome = max(
                (finding["severity"] for finding in findings), key=SEVERITY_RANK.__getitem__
            )
        output.append({
            "exact_sku": record["exact_sku"],
            "display_outcome": display_outcome,
            "findings": findings,
            "finding_count": len(findings),
        })

    findings = [finding for record in output for finding in record["findings"]]
    severity_counts = Counter(finding["severity"] for finding in findings)
    display_counts = Counter(record["display_outcome"] for record in output)
    return {
        "contract": CONTRACT,
        "status": "PASS",
        "source": dict(comparison.get("source", {})),
        "scope": {
            "product_group": "refrigerator",
            "grain": "exact_sku",
            "capacity_tolerance_cu_ft": 0,
            "epa_role": "NUMERIC_CORROBORATION_ONLY",
        },
        "decision_rule": {
            "pdp_annual_energy_missing": {"severity": "LOW", "issue_code": ANNUAL_MISSING_ISSUE},
            "pdp_energyguide_capacity_difference": {
                "severity": "MEDIUM", "issue_code": CAPACITY_MISMATCH_ISSUE,
                "comparison": "EXACT_EQUALITY_NO_TOLERANCE",
            },
            "no_findings": "PASS",
            "multiple_findings": "PRESERVE_ALL_AND_DISPLAY_HIGHEST_SEVERITY",
        },
        "counts": {
            "population": len(output),
            "finding_count": len(findings),
            "affected_sku_count": sum(bool(record["findings"]) for record in output),
            "findings_by_severity": {
                "MEDIUM": severity_counts.get("MEDIUM", 0),
                "LOW": severity_counts.get("LOW", 0),
            },
            "display": {
                key: display_counts.get(key, 0) for key in ("PASS", "MEDIUM", "LOW", "NOT_EVALUATED")
            },
        },
        "assessment_enabled": True,
        "overall_product_compliance": "NOT_EVALUATED",
        "records": output,
    }


def render_markdown(document: dict[str, Any]) -> str:
    counts = document["counts"]
    lines = [
        "# G2 refrigerator numeric assessment",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Exact SKUs | {counts['population']} |",
        f"| Findings | {counts['finding_count']} |",
        f"| Affected SKUs | {counts['affected_sku_count']} |",
        f"| MEDIUM findings | {counts['findings_by_severity']['MEDIUM']} |",
        f"| LOW findings | {counts['findings_by_severity']['LOW']} |",
        f"| UI PASS | {counts['display']['PASS']} |",
        f"| UI MEDIUM | {counts['display']['MEDIUM']} |",
        f"| UI LOW | {counts['display']['LOW']} |",
        "",
        "Capacity uses exact equality with no tolerance. EPA family values are corroboration only.",
        "",
        "| Exact SKU | Display | Issue code | Severity | PDP | EnergyGuide | EPA |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for record in document["records"]:
        for finding in record["findings"]:
            evidence = finding["evidence"]
            lines.append(
                f"| {record['exact_sku']} | {record['display_outcome']} | {finding['issue_code']} | "
                f"{finding['severity']} | {evidence['pdp_amount']} | {evidence['label_amount']} | "
                f"{evidence['epa_amount']} |"
            )
    if not counts["finding_count"]:
        lines.append("| — | — | — | — | — | — | — |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("comparison", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    comparison = json.loads(args.comparison.read_text(encoding="utf-8"))
    assessment = build_assessment(comparison)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(assessment), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

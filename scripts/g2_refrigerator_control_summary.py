"""Join existing refrigerator control outputs into per-SKU report rows.

This is a report projection.  It neither evaluates rules nor creates a product
compliance verdict; each source control retains its own outcome and findings.
"""

from collections import Counter
from typing import Any


CONTRACT = "G2_REFRIGERATOR_CONTROL_SUMMARY_V1"
SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def _index(records: Any, name: str) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list):
        raise ValueError(f"{name} records are missing")
    indexed = {record.get("exact_sku"): record for record in records if isinstance(record, dict)}
    if len(indexed) != len(records) or None in indexed:
        raise ValueError(f"{name} exact SKU records are invalid")
    return indexed


def build_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Replay all attached control sections into one exact-SKU projection."""
    if report.get("assessment_enabled") is not False:
        raise ValueError("Control summary cannot enable product compliance")
    run_id = report.get("run_id")
    rows = report.get("rows")
    if not isinstance(run_id, str) or not isinstance(rows, list):
        raise ValueError("Canonical report is invalid")
    report_skus = [row.get("exact_sku") for row in rows if isinstance(row, dict)]
    if len(report_skus) != len(rows) or len(set(report_skus)) != len(report_skus) or None in report_skus:
        raise ValueError("Canonical report exact SKU rows are invalid")

    energy = report.get("energy_star_publication", {})
    numeric = report.get("energyguide_numeric", {})
    model = report.get("energyguide_model_pattern", {})
    for section, name in ((energy, "Energy Star"), (numeric, "numeric"), (model, "model-pattern")):
        if section.get("source_run_id") != run_id:
            raise ValueError(f"{name} section belongs to another execution")

    energy_by_sku = _index(energy.get("records"), "Energy Star")
    numeric_by_sku = _index(numeric.get("records"), "numeric")
    model_by_sku = _index(model.get("records"), "model-pattern")
    expected = set(report_skus)
    if set(energy_by_sku) != expected or set(numeric_by_sku) != expected or not set(model_by_sku).issubset(expected):
        raise ValueError("Control section exact SKU coverage differs from canonical report")

    output = []
    all_findings = []
    for sku in sorted(expected):
        energy_record = energy_by_sku[sku]
        numeric_record = numeric_by_sku[sku]
        model_record = model_by_sku.get(sku)
        findings = []
        if energy_record.get("severity") in SEVERITY_RANK and energy_record.get("issue_code"):
            findings.append({"control": "ENERGY_STAR_PUBLICATION", "severity": energy_record["severity"],
                             "issue_code": energy_record["issue_code"]})
        for finding in numeric_record.get("findings", []):
            if not isinstance(finding, dict) or finding.get("severity") not in SEVERITY_RANK or not finding.get("issue_code"):
                raise ValueError("Numeric finding is invalid")
            findings.append({"control": "ENERGYGUIDE_NUMERIC", "severity": finding["severity"],
                             "issue_code": finding["issue_code"]})
        findings.sort(key=lambda item: (item["control"], item["issue_code"]))
        all_findings.extend({"exact_sku": sku, **finding} for finding in findings)
        output.append({
            "exact_sku": sku,
            "controls": {
                "energy_star_publication": {"outcome": energy_record.get("outcome"),
                                              "severity": energy_record.get("severity"),
                                              "issue_code": energy_record.get("issue_code")},
                "energyguide_numeric": {"outcome": numeric_record.get("display_outcome"),
                                          "finding_count": len(numeric_record.get("findings", []))},
                "energyguide_model_pattern": ({"outcome": model_record.get("display_outcome"),
                                                 "assessment": model_record.get("assessment")}
                                                if model_record else {"outcome": "OUT_OF_SCOPE"}),
            },
            "findings": findings,
        })
    severity_counts = Counter(finding["severity"] for finding in all_findings)
    return {
        "contract": CONTRACT,
        "source_run_id": run_id,
        "coverage": {"expected_exact_skus": len(expected), "summarized_records": len(output)},
        "counts": {"finding_count": len(all_findings),
                   "affected_sku_count": len({item["exact_sku"] for item in all_findings}),
                   "findings_by_severity": {key: severity_counts.get(key, 0) for key in ("HIGH", "MEDIUM", "LOW")}},
        "overall_product_compliance": "NOT_EVALUATED",
        "records": output,
    }


def add_control_summary(report: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    if summary.get("contract") != CONTRACT or summary.get("source_run_id") != report.get("run_id"):
        raise ValueError("Control summary belongs to another execution")
    if summary.get("overall_product_compliance") != "NOT_EVALUATED":
        raise ValueError("Control summary cannot enable product compliance")
    rows = {row.get("exact_sku"): row for row in report.get("rows", [])}
    records = _index(summary.get("records"), "control summary")
    if set(rows) != set(records):
        raise ValueError("Control summary SKU coverage differs from canonical report")
    replay = []
    for sku in sorted(rows):
        row = records[sku]
        rows[sku]["refrigerator_control_summary"] = {"controls": row["controls"], "findings": row["findings"]}
        replay.extend({"exact_sku": sku, **finding} for finding in row["findings"])
    severity_counts = Counter(finding["severity"] for finding in replay)
    expected_counts = {"finding_count": len(replay), "affected_sku_count": len({x["exact_sku"] for x in replay}),
                       "findings_by_severity": {key: severity_counts.get(key, 0) for key in ("HIGH", "MEDIUM", "LOW")}}
    if summary.get("counts") != expected_counts:
        raise ValueError("Control summary counts do not replay")
    report["refrigerator_control_summary"] = {
        key: summary[key]
        for key in ("contract", "source_run_id", "coverage", "counts", "overall_product_compliance", "records")
    }
    return report

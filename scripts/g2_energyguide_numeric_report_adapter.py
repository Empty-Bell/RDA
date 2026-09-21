"""Attach a complete same-run numeric assessment as a canonical report section."""

import hashlib
from pathlib import Path
from typing import Any


ASSESSMENT_CONTRACT = "G2_ENERGYGUIDE_NUMERIC_ASSESSMENT_V1"
OUTCOMES = {"PASS", "LOW", "MEDIUM", "NOT_EVALUATED"}


def attach_numeric_assessment(
    bundle: dict[str, Any], assessment: dict[str, Any], assessment_path: str | Path,
    *, artifact_reference: str | None = None,
) -> dict[str, Any]:
    if assessment.get("contract") != ASSESSMENT_CONTRACT or assessment.get("status") != "PASS":
        raise ValueError("Numeric assessment contract is invalid")
    if assessment.get("assessment_enabled") is not True:
        raise ValueError("Numeric assessment is not enabled")
    run_id = bundle["manifest"]["run_id"]
    source = assessment.get("source", {})
    if source.get("execution_run_id") != run_id:
        raise ValueError("Numeric assessment execution ID differs from canonical bundle")
    expected = {product["exact_sku"] for product in bundle["products"]}
    records = assessment.get("records")
    if not isinstance(records, list):
        raise ValueError("Numeric assessment records are missing")
    observed = [record.get("exact_sku") for record in records if isinstance(record, dict)]
    if len(observed) != len(records) or len(observed) != len(set(observed)) or set(observed) != expected:
        raise ValueError("Numeric assessment SKU coverage differs from canonical bundle")
    display = {}
    for record in records:
        outcome = record.get("display_outcome")
        if outcome not in OUTCOMES:
            raise ValueError("Numeric assessment display outcome is invalid")
        display[outcome] = display.get(outcome, 0) + 1
    expected_counts = {key: display.get(key, 0) for key in ("PASS", "MEDIUM", "LOW", "NOT_EVALUATED")}
    if assessment.get("counts", {}).get("display") != expected_counts:
        raise ValueError("Numeric assessment display counts do not replay")
    path = Path(assessment_path)
    return {
        "contract": ASSESSMENT_CONTRACT,
        "source_run_id": run_id,
        "source_artifact": {
            "path": artifact_reference or path.as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        },
        "coverage": {"expected_exact_skus": len(expected), "evaluated_records": len(records)},
        "counts": dict(assessment["counts"]),
        "overall_product_compliance": "NOT_EVALUATED",
        "records": [
            {"exact_sku": record["exact_sku"], "display_outcome": record["display_outcome"],
             "findings": record["findings"]}
            for record in sorted(records, key=lambda item: item["exact_sku"])
        ],
    }


def add_numeric_section(report: dict[str, Any], section: dict[str, Any]) -> dict[str, Any]:
    if report.get("assessment_enabled") is not False:
        raise ValueError("Numeric section cannot enable whole-product compliance")
    if section.get("source_run_id") != report.get("run_id"):
        raise ValueError("Numeric section belongs to another execution")
    report_skus = {row.get("exact_sku") for row in report.get("rows", [])}
    section_skus = {row.get("exact_sku") for row in section.get("records", [])}
    if not report_skus or report_skus != section_skus:
        raise ValueError("Numeric section SKU coverage differs from canonical report")
    report["energyguide_numeric"] = section
    return report

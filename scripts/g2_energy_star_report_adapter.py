"""Attach a same-run Energy Star assessment as a separate report section."""

from collections import Counter
import hashlib
from pathlib import Path
from typing import Any


ASSESSMENT_CONTRACT = "G2_ENERGY_STAR_THREE_POINT_ASSESSMENT_V1"
SOURCE_CONTRACT = "G2_ENERGY_STAR_DIRECT_SOURCE_DECLARATIONS_V1"
OUTCOMES = {"PASS", "NO_FINDING", "LOW", "HIGH", "NOT_EVALUATED"}


def attach_energy_star_assessment(
    bundle: dict[str, Any], assessment: dict[str, Any], source_manifest: dict[str, Any],
    assessment_path: str | Path, *, github_run_id: str, artifact_reference: str | None = None,
) -> dict[str, Any]:
    """Build a distinct report section only when provenance and coverage align."""
    if source_manifest.get("contract") != SOURCE_CONTRACT or source_manifest.get("status") != "PASS":
        raise ValueError("Energy Star source manifest is invalid")
    run_id = bundle["manifest"]["run_id"]
    if assessment.get("contract") != ASSESSMENT_CONTRACT:
        raise ValueError("Energy Star assessment contract is invalid")
    if assessment.get("source_run_id") != run_id or source_manifest.get("run_id") != run_id:
        raise ValueError("Energy Star and canonical bundle execution IDs differ")
    if source_manifest.get("github_run_id") != github_run_id:
        raise ValueError("Energy Star and canonical bundle GitHub run IDs differ")
    if source_manifest.get("git_sha") != bundle["manifest"].get("git_sha"):
        raise ValueError("Energy Star and canonical bundle source commits differ")

    expected = {product["exact_sku"] for product in bundle["products"]}
    records = assessment.get("records")
    if not isinstance(records, list):
        raise ValueError("Energy Star assessment records are missing")
    observed = [record.get("exact_sku") for record in records if isinstance(record, dict)]
    if len(observed) != len(records) or len(observed) != len(set(observed)) or set(observed) != expected:
        raise ValueError("Energy Star exact SKU coverage differs from canonical bundle")
    if assessment.get("coverage") != {
        "expected_exact_skus": len(expected), "evaluated_records": len(expected)
    }:
        raise ValueError("Energy Star assessment does not report complete exact SKU coverage")

    counts = Counter(record.get("outcome") for record in records)
    if not set(counts).issubset(OUTCOMES) or dict(sorted(counts.items())) != assessment.get("counts"):
        raise ValueError("Energy Star outcome counts do not replay from assessment records")
    path = Path(assessment_path)
    return {
        "contract": ASSESSMENT_CONTRACT,
        "source_run_id": run_id,
        "source_github_run_id": source_manifest["github_run_id"],
        "source_git_sha": source_manifest["git_sha"],
        "source_artifact": {
            "path": artifact_reference or path.as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        },
        "coverage": dict(assessment["coverage"]),
        "counts": dict(assessment["counts"]),
        "display_counts": {
            "PASS": counts.get("PASS", 0) + counts.get("NO_FINDING", 0),
            "LOW": counts.get("LOW", 0),
            "HIGH": counts.get("HIGH", 0),
            "NOT_EVALUATED": counts.get("NOT_EVALUATED", 0),
        },
        "review_clusters": assessment.get("review_clusters", {}),
        "overall_product_compliance": "NOT_EVALUATED",
        "records": [
            {"exact_sku": record["exact_sku"], "outcome": record["outcome"],
             "severity": record.get("severity"), "issue_code": record.get("issue_code")}
            for record in sorted(records, key=lambda item: item["exact_sku"])
        ],
    }


def add_energy_star_section(report: dict[str, Any], section: dict[str, Any]) -> dict[str, Any]:
    """Attach the vertical slice without changing canonical assessment totals."""
    if section.get("source_run_id") != report.get("run_id"):
        raise ValueError("Energy Star report section belongs to another execution")
    skus = [row.get("exact_sku") for row in report.get("rows", [])]
    energy_skus = [row.get("exact_sku") for row in section.get("records", [])]
    if len(skus) != len(set(skus)) or set(skus) != set(energy_skus):
        raise ValueError("Energy Star report section SKU coverage differs from canonical report")
    if report.get("assessment_enabled") is not False or section.get("overall_product_compliance") != "NOT_EVALUATED":
        raise ValueError("Energy Star section cannot enable overall compliance")
    report["energy_star_publication"] = section
    return report

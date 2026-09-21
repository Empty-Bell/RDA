"""Attach a limited reviewed EnergyGuide model-pattern assessment to the canonical report."""

import hashlib
from pathlib import Path
from typing import Any

CONTRACT = "G2_ENERGYGUIDE_REVIEW_BOUND_MODEL_PATTERN_ASSESSMENT_V1"


def attach_model_pattern_assessment(bundle: dict[str, Any], assessment: dict[str, Any], path: str | Path) -> dict[str, Any]:
    if assessment.get("contract") != CONTRACT or assessment.get("status") != "PASS" or assessment.get("assessment_enabled") is not True:
        raise ValueError("Model-pattern assessment contract is invalid")
    if assessment.get("source", {}).get("execution_run_id") != bundle.get("manifest", {}).get("run_id"):
        raise ValueError("Model-pattern assessment execution ID differs from canonical bundle")
    records = assessment.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Model-pattern assessment records are missing")
    skus = [record.get("exact_sku") for record in records]
    bundle_skus = {product.get("exact_sku") for product in bundle.get("products", [])}
    if len(skus) != len(set(skus)) or not set(skus).issubset(bundle_skus):
        raise ValueError("Model-pattern assessment SKU scope differs from canonical bundle")
    counts = {key: sum(record.get("display_outcome") == key for record in records) for key in ("PASS", "NOT_EVALUATED")}
    if assessment.get("counts", {}).get("display") != counts:
        raise ValueError("Model-pattern assessment counts do not replay")
    artifact = Path(path)
    return {"contract": CONTRACT, "source_run_id": bundle["manifest"]["run_id"],
            "source_artifact": {"path": artifact.as_posix(), "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()},
            "coverage": {"reviewed_exact_skus": len(records)}, "counts": assessment["counts"],
            "overall_product_compliance": "NOT_EVALUATED",
            "records": [{key: record[key] for key in ("exact_sku", "display_outcome", "assessment", "matching_patterns", "label_pdf_sha256")} for record in records]}


def add_model_pattern_section(report: dict[str, Any], section: dict[str, Any]) -> dict[str, Any]:
    if report.get("assessment_enabled") is not False or section.get("source_run_id") != report.get("run_id"):
        raise ValueError("Model-pattern section cannot enable or cross canonical product compliance")
    report["energyguide_model_pattern"] = section
    return report

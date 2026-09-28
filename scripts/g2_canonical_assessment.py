"""Promote approved, same-run refrigerator controls into canonical assessments."""

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from regaudit.contracts import validate_bundle


RULE_VERSION = "G2_REFRIGERATOR_APPROVED_CONTROLS_V1"
CONTROLS = {
    "energy_star": ("EPA", "ENERGY_STAR_PUBLICATION", "G2_ENERGY_STAR_THREE_POINT_ASSESSMENT_V1"),
    "numeric": ("FTC", "ENERGYGUIDE_NUMERIC", "G2_ENERGYGUIDE_NUMERIC_ASSESSMENT_V1"),
    "model": ("FTC", "ENERGYGUIDE_MODEL_PREFIX", "G2_ENERGYGUIDE_MODEL_PATTERN_ASSESSMENT_V1"),
}


def promote(
    bundle: dict[str, Any],
    star: dict[str, Any],
    numeric: dict[str, Any],
    model: dict[str, Any],
    epa_capture_root: Path,
    add_evidence: Callable[..., tuple[str, str]],
) -> dict[str, Any]:
    """Require complete control coverage and retain original PDP, label and EPA bytes."""
    run_id = bundle["manifest"]["run_id"]
    expected = {product["exact_sku"] for product in bundle["products"]}
    sources = {}
    for name, data in (("energy_star", star), ("numeric", numeric), ("model", model)):
        records = data.get("records")
        if not isinstance(records, list):
            raise ValueError(f"{name} records missing")
        index = {record["exact_sku"]: record for record in records}
        if len(index) != len(records) or set(index) != expected:
            raise ValueError(f"{name} control coverage differs from population")
        sources[name] = index
    if star.get("source_run_id") != run_id or numeric.get("source", {}).get("execution_run_id") != run_id or model.get("source", {}).get("execution_run_id") != run_id:
        raise ValueError("Control assessment belongs to another execution")

    facts = {(item["exact_sku"], item["kind"]): item for item in bundle["facts"]}
    if set(facts) != {(sku, kind) for sku in expected for kind in ("PDP", "ENERGYGUIDE")}:
        raise ValueError("Canonical PDP/label facts are incomplete")
    manifest = json.loads((epa_capture_root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("run_id") != run_id or manifest.get("status") != "PASS":
        raise ValueError("EPA current index capture does not match execution")
    pages = [entry for entry in manifest["sources"] if entry["name"].startswith("page-")]
    if not pages:
        raise ValueError("EPA current index pages missing")
    for page in pages:
        raw = (epa_capture_root / page["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != page["body_sha256"] or page["status"] != 200:
            raise ValueError("EPA source page digest or status invalid")
    pages.sort(key=lambda item: item["name"])

    bundle["assessments"] = []
    for sku in sorted(expected):
        pdp_ids = facts[sku, "PDP"]["evidence_ids"]
        label_ids = facts[sku, "ENERGYGUIDE"]["evidence_ids"]
        pf_ids = [item["evidence_id"] for item in bundle["evidence"] if item["sku"] == sku and item["evidence_type"] == "projected-public-pf-response"]
        if not pdp_ids or not label_ids or not pf_ids:
            raise ValueError("PDP, label or PLP evidence missing")
        epa_ids = []
        for page in pages:
            item_id, _ = add_evidence((epa_capture_root / page["file"]).read_bytes(), page["url"], sku, "epa-current-index-source-page", manifest["captured_at"])
            epa_ids.append(item_id)

        def append(control: str, finding: dict[str, Any] | None, *, reason: str, expected_value: Any, observed: Any, evidence_ids: list[str]) -> None:
            domain, control_id, rule_id = CONTROLS[control]
            bundle["assessments"].append({
                "assessment_id": f"a-{len(bundle['assessments'])}",
                "run_id": run_id, "product_group": "refrigerator", "exact_sku": sku,
                "regulatory_domain": domain, "control_id": control_id,
                "rule_id": rule_id, "rule_version": RULE_VERSION,
                "assessment_status": "FINDING" if finding else "NO_EXCEPTION_OBSERVED",
                "severity": finding["severity"] if finding else None,
                "issue_code": finding["issue_code"] if finding else None,
                "reason": reason, "expected": expected_value, "observed": observed,
                "evidence_ids": list(dict.fromkeys(evidence_ids)),
                "automatic_final_legal_conclusion": False,
            })

        es = sources["energy_star"][sku]
        if es["outcome"] == "NOT_EVALUATED":
            raise ValueError("Energy Star control remains unevaluated")
        star_finding = es if es["outcome"] in ("HIGH", "LOW") else None
        if es["outcome"] not in ("PASS", "NO_FINDING", "HIGH", "LOW"):
            raise ValueError("Unexpected Energy Star control outcome")
        append("energy_star", star_finding, reason="ENERGY STAR publication points compared with EPA Current index", expected_value="Samsung publication matches current EPA registration", observed={"publication_points": es["publication_points"], "epa_current_index_registration": es["epa_current_index_registration"], "outcome": es["outcome"]}, evidence_ids=[*pf_ids, *pdp_ids, *epa_ids])

        num = sources["numeric"][sku]
        if num["display_outcome"] == "NOT_EVALUATED" or num["finding_count"] != len(num["findings"]):
            raise ValueError("Numeric control incomplete")
        for finding in num["findings"] or [None]:
            append("numeric", finding, reason=finding["evidence"]["reason"] if finding else "PDP and EnergyGuide numeric control passed", expected_value="PDP annual energy and capacity align with EnergyGuide", observed=finding["evidence"] if finding else {"outcome": "PASS"}, evidence_ids=[*pdp_ids, *label_ids])

        match = sources["model"][sku]
        if match["display_outcome"] != "PASS" or not match["matching_patterns"]:
            raise ValueError("EnergyGuide model control is unresolved")
        append("model", None, reason="At least one complete label model token matches approved PDP prefix", expected_value="Any printed label model matches normalized PDP prefix", observed={"normalized_pdp_model": match["normalized_identifier"], "matching_patterns": match["matching_patterns"], "label_pdf_sha256": match["label_pdf_sha256"]}, evidence_ids=[*pdp_ids, *label_ids])

    bundle["manifest"].update(rule_version=RULE_VERSION, assessment_enabled=True, overall_execution_status="SUCCESS")
    validate_bundle(bundle, assessed=True)
    counts = Counter(item["assessment_status"] for item in bundle["assessments"])
    if counts["FINDING"] != sum(record["finding_count"] for record in sources["numeric"].values()) + sum(record["outcome"] in ("HIGH", "LOW") for record in sources["energy_star"].values()):
        raise ValueError("Canonical finding count differs from approved controls")
    return bundle

"""Approved product/finding counts; no rule evaluation or summary severity."""

import copy
from typing import Any
from .contracts import validate_bundle


def summarize_bundle(
    bundle: dict[str, Any], *, synthetic_assessments: bool = False
) -> dict[str, Any]:
    validate_bundle(bundle, synthetic_assessments=synthetic_assessments)
    rows: dict[str, Any] = {
        p["exact_sku"]: {
            "exact_sku": p["exact_sku"],
            "listings": copy.deepcopy(p["listings"]),
            "assessments": [],
            "energyguide_source_observations": [],
        }
        for p in bundle["products"]
    }
    groups = {listing["product_group"] for p in bundle["products"] for listing in p["listings"]}
    findings = [a for a in bundle["assessments"] if a["assessment_status"] == "FINDING"]
    for assessment in bundle["assessments"]:
        rows[assessment["exact_sku"]]["assessments"].append(copy.deepcopy(assessment))
    for fact in bundle["facts"]:
        if fact["kind"] != "ENERGYGUIDE":
            continue
        observations = fact["observations"]
        rows[fact["exact_sku"]]["energyguide_source_observations"].append({
            "document_url": copy.deepcopy(observations["document_url"]),
            "document_sha256": copy.deepcopy(observations["document_sha256"]),
            "document_status": copy.deepcopy(observations["document_status"]),
            "annual_energy_kwh": copy.deepcopy(observations["annual_energy_kwh"]),
            "capacity": copy.deepcopy(observations["capacity"]),
            "evidence_ids": copy.deepcopy(fact["evidence_ids"]),
        })
    for row in rows.values():
        row["energyguide_source_observations"].sort(
            key=lambda item: str(item["document_sha256"].get("value", ""))
        )
    by_group: dict[str, Any] = {}
    for group in sorted(groups):
        members = {
            p["exact_sku"]
            for p in bundle["products"]
            if any(listing["product_group"] == group for listing in p["listings"])
        }
        matches = [a for a in findings if a["product_group"] == group]
        by_group[group] = {
            "product_count": len(members),
            "finding_count": len(matches),
            "affected_sku_count": len({a["exact_sku"] for a in matches}),
        }
    return {
        "run_id": bundle["manifest"]["run_id"],
        "assessment_enabled": False,
        "synthetic": synthetic_assessments,
        "counts": {
            "product_count": len(rows),
            "finding_count": len(findings),
            "affected_sku_count": len({a["exact_sku"] for a in findings}),
        },
        "group_subtotals_overlap": True,
        "by_group": by_group,
        "rows": [rows[key] for key in sorted(rows)],
    }

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
        }
        for p in bundle["products"]
    }
    groups = {listing["product_group"] for p in bundle["products"] for listing in p["listings"]}
    findings = [a for a in bundle["assessments"] if a["assessment_status"] == "FINDING"]
    for assessment in bundle["assessments"]:
        rows[assessment["exact_sku"]]["assessments"].append(copy.deepcopy(assessment))
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

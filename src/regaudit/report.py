"""Approved product/finding counts; no rule evaluation or summary severity."""

import copy
from typing import Any
from .contracts import ContractError, validate_bundle


def _energyguide_source_observations(bundle: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {
        product["exact_sku"]: [] for product in bundle["products"]
    }
    for fact in bundle["facts"]:
        if fact["kind"] != "ENERGYGUIDE":
            continue
        observations = fact["observations"]
        rows[fact["exact_sku"]].append(
            {
                "document_url": copy.deepcopy(observations["document_url"]),
                "document_sha256": copy.deepcopy(observations["document_sha256"]),
                "document_status": copy.deepcopy(observations["document_status"]),
                "annual_energy_kwh": copy.deepcopy(observations["annual_energy_kwh"]),
                "capacity": copy.deepcopy(observations["capacity"]),
                "evidence_ids": copy.deepcopy(fact["evidence_ids"]),
            }
        )
    for entries in rows.values():
        entries.sort(key=lambda item: str(item["document_sha256"].get("value", "")))
    return rows


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
    for sku, observations in _energyguide_source_observations(bundle).items():
        rows[sku]["energyguide_source_observations"] = observations
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


def verify_report_source_observations(bundle: dict[str, Any], report: dict[str, Any]) -> None:
    """Replay report EnergyGuide entries from the stored same-run source facts."""
    validate_bundle(bundle)
    rows = report.get("rows")
    if not isinstance(rows, list):
        raise ContractError("Report rows missing")
    actual: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("exact_sku"), str):
            raise ContractError("Report row identity invalid")
        sku = row["exact_sku"]
        if sku in actual or not isinstance(row.get("energyguide_source_observations"), list):
            raise ContractError("Report EnergyGuide source observation rows invalid")
        actual[sku] = row["energyguide_source_observations"]
    if actual != _energyguide_source_observations(bundle):
        raise ContractError("Report EnergyGuide source observations do not replay from bundle")

"""Compare PDP and selected EnergyGuide numbers without issuing findings."""

import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
from typing import Any
import zipfile


CONTRACT = "G2_ENERGYGUIDE_PDP_NUMERIC_COMPARISON_OBSERVATION_V1"


def _one_json(archive: zipfile.ZipFile, suffix: str) -> dict[str, Any]:
    names = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise ValueError(f"Artifact must contain exactly one {suffix}")
    return json.loads(archive.read(names[0]))


def _amount(observation: dict[str, Any], expected_units: set[str]) -> Decimal | None:
    if observation.get("state") != "VALUE":
        return None
    value = observation.get("value")
    if not isinstance(value, dict) or value.get("unit") not in expected_units:
        raise ValueError("Comparable measurement has an unexpected unit or shape")
    try:
        return Decimal(str(value["amount"]))
    except (KeyError, ValueError, TypeError):
        raise ValueError("Comparable measurement amount is invalid") from None


def _compare(
    pdp: dict[str, Any],
    label: dict[str, Any],
    pdp_units: set[str],
    label_units: set[str],
) -> dict[str, Any]:
    pdp_amount = _amount(pdp, pdp_units)
    label_amount = _amount(label, label_units)
    if pdp_amount is None or label_amount is None:
        return {
            "state": "NOT_COMPARABLE",
            "reason": "PDP_VALUE_MISSING" if pdp_amount is None else "LABEL_VALUE_MISSING",
            "pdp_amount": float(pdp_amount) if pdp_amount is not None else None,
            "label_amount": float(label_amount) if label_amount is not None else None,
            "delta_pdp_minus_label": None,
        }
    delta = pdp_amount - label_amount
    return {
        "state": "EQUAL" if delta == 0 else "DIFFERENT",
        "reason": "EXACT_NUMERIC_EQUALITY" if delta == 0 else "OBSERVED_NUMERIC_DIFFERENCE",
        "pdp_amount": float(pdp_amount),
        "label_amount": float(label_amount),
        "delta_pdp_minus_label": float(delta),
    }


def _epa_measurement(record: dict[str, Any] | None, field: str) -> dict[str, Any]:
    if record is None:
        return {"state": "NOT_REQUESTED", "amount": None}
    value = record.get(field)
    if not isinstance(value, dict) or not isinstance(value.get("state"), str):
        raise ValueError("EPA numeric enrichment measurement is invalid")
    return {"state": value["state"], "amount": value.get("amount")}


def _relation(left: float | None, right: float | None) -> str:
    if left is None or right is None:
        return "NOT_COMPARABLE"
    return "EQUAL" if Decimal(str(left)) == Decimal(str(right)) else "DIFFERENT"


def build_comparison_from_inputs(
    bundle: dict[str, Any], replay: dict[str, Any], epa: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if replay.get("contract") != "G2_LABEL_ANNOTATION_REPLAY_V1" or replay.get("status") != "PASS":
        raise ValueError("Successful label selection replay is required")
    run_id = bundle.get("manifest", {}).get("run_id")
    if replay.get("source", {}).get("execution_run_id") != run_id:
        raise ValueError("Selection replay and bundle run IDs differ")

    products = bundle.get("products")
    if not isinstance(products, list) or not products:
        raise ValueError("Product population is unavailable")
    product_skus = {product.get("exact_sku") for product in products}
    if None in product_skus or len(product_skus) != len(products):
        raise ValueError("Product population exact-SKU grain is invalid")
    pdp_facts = {
        fact["exact_sku"]: fact
        for fact in bundle.get("facts", [])
        if fact.get("kind") == "PDP"
    }
    annual = {
        row["exact_sku"]: row["annual_energy_observation"]
        for row in replay["label_selection_summary"]["records"]
    }
    capacity = {
        row["exact_sku"]: row["capacity_observation"]
        for row in replay["capacity_selection_summary"]["records"]
    }
    epa_records = None
    if epa is not None:
        if (epa.get("contract") != "G2_EPA_REFRIGERATOR_NUMERIC_ENRICHMENT_V1"
                or epa.get("status") != "PASS"
                or epa.get("source_run_id") != run_id
                or epa.get("assessment_enabled") is not False):
            raise ValueError("EPA numeric enrichment provenance is invalid")
        epa_records = {row["exact_sku"]: row for row in epa.get("records", [])}
        if set(epa_records) != product_skus:
            raise ValueError("EPA numeric enrichment does not cover the exact-SKU population")
    if set(pdp_facts) != product_skus or set(annual) != product_skus or set(capacity) != product_skus:
        raise ValueError("Comparison inputs do not cover the exact-SKU population")

    records = []
    for sku in sorted(product_skus):
        observations = pdp_facts[sku].get("observations", {})
        annual_result = _compare(
            observations.get("pdp_annual_energy_kwh", {}),
            annual[sku],
            {"kWh/year"},
            {"kWh/year"},
        )
        capacity_result = _compare(
            observations.get("pdp_capacity", {}),
            capacity[sku],
            {"cu ft"},
            {"Cubic Feet", "cubic feet"},
        )
        epa_row = epa_records.get(sku) if epa_records is not None else None
        epa_annual = _epa_measurement(epa_row, "annual_energy_kwh")
        epa_capacity = _epa_measurement(epa_row, "capacity_cu_ft")
        annual_result["epa_amount"] = epa_annual["amount"]
        annual_result["epa_state"] = epa_annual["state"]
        annual_result["label_epa_relation"] = _relation(annual_result["label_amount"], epa_annual["amount"])
        annual_result["pdp_epa_relation"] = _relation(annual_result["pdp_amount"], epa_annual["amount"])
        capacity_result["epa_amount"] = epa_capacity["amount"]
        capacity_result["epa_state"] = epa_capacity["state"]
        capacity_result["label_epa_relation"] = _relation(capacity_result["label_amount"], epa_capacity["amount"])
        capacity_result["pdp_epa_relation"] = _relation(capacity_result["pdp_amount"], epa_capacity["amount"])
        records.append({
            "exact_sku": sku,
            "annual_energy_kwh": annual_result,
            "capacity_cu_ft": capacity_result,
            "assessment": "NOT_EVALUATED",
        })
    annual_counts = Counter(row["annual_energy_kwh"]["state"] for row in records)
    capacity_counts = Counter(row["capacity_cu_ft"]["state"] for row in records)
    return {
        "contract": CONTRACT,
        "status": "PASS",
        "source": {
            "artifact_zip": "IN_MEMORY_SAME_RUN_BUNDLE",
            "execution_run_id": run_id,
            "git_sha": bundle.get("manifest", {}).get("git_sha"),
        },
        "scope": {
            "product_group": "refrigerator",
            "grain": "exact_sku",
            "comparison_mode": "OBSERVATION_ONLY_NO_TOLERANCE_NO_FINDINGS",
            "epa_numeric_enrichment": epa is not None,
        },
        "counts": {
            "population": len(records),
            "annual_energy": {key: annual_counts.get(key, 0) for key in ("EQUAL", "DIFFERENT", "NOT_COMPARABLE")},
            "capacity": {key: capacity_counts.get(key, 0) for key in ("EQUAL", "DIFFERENT", "NOT_COMPARABLE")},
        },
        "records": records,
        "assessment_enabled": False,
        "overall_product_compliance": "NOT_EVALUATED",
    }


def build_comparison(
    artifact_zip: Path,
    selection_replay_path: Path,
    epa_numeric_path: Path | None = None,
) -> dict[str, Any]:
    replay = json.loads(selection_replay_path.read_text(encoding="utf-8"))
    with zipfile.ZipFile(artifact_zip) as archive:
        bundle = _one_json(archive, "/bundle.json")
    epa = json.loads(epa_numeric_path.read_text(encoding="utf-8")) if epa_numeric_path else None
    document = build_comparison_from_inputs(bundle, replay, epa)
    document["source"]["artifact_zip"] = artifact_zip.name
    return document


def render_markdown(document: dict[str, Any]) -> str:
    annual = document["counts"]["annual_energy"]
    capacity = document["counts"]["capacity"]
    different = [
        row for row in document["records"]
        if row["annual_energy_kwh"]["state"] == "DIFFERENT"
        or row["capacity_cu_ft"]["state"] == "DIFFERENT"
    ]
    lines = [
        "# G2 refrigerator PDP / EnergyGuide numeric comparison",
        "",
        "This output records equality and differences only. It does not apply a tolerance, severity or compliance finding.",
        "",
        "| Field | Equal | Different | Not comparable |",
        "|---|---:|---:|---:|",
        f"| Annual energy (kWh/year) | {annual['EQUAL']} | {annual['DIFFERENT']} | {annual['NOT_COMPARABLE']} |",
        f"| Capacity (cu ft) | {capacity['EQUAL']} | {capacity['DIFFERENT']} | {capacity['NOT_COMPARABLE']} |",
        "",
    ]
    if document["scope"].get("epa_numeric_enrichment"):
        annual_epa = Counter(row["annual_energy_kwh"]["label_epa_relation"] for row in document["records"])
        capacity_epa = Counter(row["capacity_cu_ft"]["label_epa_relation"] for row in document["records"])
        lines.extend([
            "## EnergyGuide / EPA numeric corroboration",
            "",
            "| Field | Equal | Different | Not comparable |",
            "|---|---:|---:|---:|",
            f"| Annual energy (kWh/year) | {annual_epa['EQUAL']} | {annual_epa['DIFFERENT']} | {annual_epa['NOT_COMPARABLE']} |",
            f"| Capacity (cu ft) | {capacity_epa['EQUAL']} | {capacity_epa['DIFFERENT']} | {capacity_epa['NOT_COMPARABLE']} |",
            "",
        ])
    lines.extend([
        "## Observed differences",
        "",
        "| Exact SKU | Field | PDP | EnergyGuide | EPA | PDP − label |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in different:
        for field, label in (("annual_energy_kwh", "Annual energy"), ("capacity_cu_ft", "Capacity")):
            result = row[field]
            if result["state"] == "DIFFERENT":
                lines.append(
                    f"| {row['exact_sku']} | {label} | {result['pdp_amount']} | {result['label_amount']} | {result['epa_amount']} | {result['delta_pdp_minus_label']} |"
                )
    if not different:
        lines.append("| — | — | — | — | — | — |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", type=Path)
    parser.add_argument("--selection-replay", type=Path, required=True)
    parser.add_argument("--epa-numeric", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    document = build_comparison(args.artifact_zip, args.selection_replay, args.epa_numeric)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(document), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

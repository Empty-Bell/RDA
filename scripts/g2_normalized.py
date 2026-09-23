"""Adapt collected PDP source records into source-only normalized observations."""

from typing import Any

from regaudit.normalization import normalize_pdp


def normalize_source_pdp(
    specs: dict[str, Any], claim_facts: dict[str, Any] | None
) -> dict[str, Any]:
    """Normalize one exact-SKU source record without making an assessment."""
    exact_sku = specs.get("exact_sku")
    if not isinstance(exact_sku, str) or not exact_sku:
        raise ValueError("PDP source record must declare exact_sku")
    for field in (
        "energy_consumption_raw",
        "capacity_raw",
        "energy_star_spec_claim_raw",
    ):
        if not isinstance(specs.get(field), list):
            raise ValueError("PDP source record has invalid " + field)

    if claim_facts is None:
        normalized = normalize_pdp(
            specs, [], [], allow_refrigerator_energy_rows=True
        )
        normalized["claim_channel_collection"] = "NOT_COLLECTED_FOR_THIS_PDP_SAMPLE"
        return normalized

    if claim_facts.get("exact_sku") != exact_sku:
        raise ValueError("Claim source record exact_sku does not match PDP source record")
    for field in (
        "plp_energy_star_flag_raw",
        "pdp_structured_energy_star_fields_raw",
    ):
        if field not in claim_facts:
            raise ValueError("Claim source record is missing " + field)
    structured = claim_facts["pdp_structured_energy_star_fields_raw"]
    if not isinstance(structured, list) or not all(isinstance(item, dict) for item in structured):
        raise ValueError("Claim source record has invalid structured PDP fields")

    normalized = normalize_pdp(
        specs,
        [claim_facts["plp_energy_star_flag_raw"]],
        structured,
        allow_refrigerator_energy_rows=True,
    )
    normalized["claim_channel_collection"] = "COLLECTED_SOURCE_RECORD"
    return normalized

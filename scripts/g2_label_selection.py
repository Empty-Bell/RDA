"""Conservative annual-energy selection from preserved EnergyGuide candidates."""

from typing import Any


def unavailable(reason: str) -> dict[str, Any]:
    return {
        "observation": {"state": "NOT_OBSERVED", "value": None, "error": None},
        "reason": reason,
    }


def select_annual_energy(candidates: dict[str, Any], layout: dict[str, Any]) -> dict[str, Any]:
    """Select only a single caption-linked, explicit kWh candidate on one panel."""
    if candidates.get("pdf_sha256") != layout.get("pdf_sha256"):
        raise ValueError("Candidate and layout PDF provenance differ")
    energies = candidates.get("energy_candidates_raw")
    layouts = layout.get("annual_layout_candidates")
    if not isinstance(energies, list) or not isinstance(layouts, list):
        raise ValueError("Candidate collections are invalid")
    annual = [entry for entry in energies if entry.get("role") == "ANNUAL_CAPTION_CONTEXT"]
    associated = [entry for entry in layouts if entry.get("nearest_proposal_raw") is not None]
    if len(annual) != 1 or len(associated) != 1:
        return unavailable("MISSING_OR_AMBIGUOUS_ANNUAL_CAPTION_ASSOCIATION")
    proposal = associated[0]["nearest_proposal_raw"]
    if not isinstance(proposal, dict) or proposal.get("value_raw") != annual[0].get("value_raw"):
        return unavailable("TEXT_AND_LAYOUT_CANDIDATES_DO_NOT_UNIQUELY_AGREE")
    raw_value = annual[0].get("value_raw")
    try:
        amount = float(raw_value)
    except (TypeError, ValueError):
        return unavailable("UNSUPPORTED_ANNUAL_NUMBER_ENCODING")
    if amount < 0:
        return unavailable("UNSUPPORTED_ANNUAL_NUMBER_ENCODING")
    return {
        "observation": {
            "state": "VALUE",
            "value": {
                "amount": amount,
                "unit": "kWh/year",
                "raw": annual[0].get("matched_text"),
            },
            "error": None,
        },
        "reason": "UNIQUE_EXPLICIT_KWH_WITH_ANNUAL_CAPTION_AND_LAYOUT_ASSOCIATION",
        "candidate": annual[0],
        "layout": associated[0],
    }

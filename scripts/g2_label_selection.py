"""Conservative annual-energy selection from preserved EnergyGuide candidates."""

from typing import Any
import math
import re


def unavailable(reason: str) -> dict[str, Any]:
    return {
        "observation": {"state": "NOT_OBSERVED", "value": None, "error": None},
        "reason": reason,
    }


def select_annual_energy(candidates: dict[str, Any], layout: dict[str, Any], review: dict[str, Any] | None = None) -> dict[str, Any]:
    """Select only a single caption-linked, explicit kWh candidate on one panel."""
    digest = candidates.get("pdf_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Candidate PDF provenance is invalid")
    if digest != layout.get("pdf_sha256"):
        raise ValueError("Candidate and layout PDF provenance differ")
    if review is None:
        return unavailable("DOCUMENT_AND_PANEL_REVIEW_REQUIRED")
    if review.get("pdf_sha256") != digest:
        raise ValueError("Review PDF provenance differs")
    if review.get("document_count") != 1 or review.get("all_pages_reviewed") is not True or review.get("us_panel_verified") is not True:
        return unavailable("DOCUMENT_AND_PANEL_REVIEW_REQUIRED")
    energies = candidates.get("energy_candidates_raw")
    layouts = layout.get("annual_layout_candidates")
    if not isinstance(energies, list) or not isinstance(layouts, list):
        raise ValueError("Candidate collections are invalid")
    annual = [entry for entry in energies if entry.get("role") == "ANNUAL_CAPTION_CONTEXT"]
    associated = [entry for entry in layouts if entry.get("nearest_proposal_raw") is not None]
    if len(annual) != 1 or len(associated) != 1:
        return unavailable("MISSING_OR_AMBIGUOUS_ANNUAL_CAPTION_ASSOCIATION")
    proposal = associated[0]["nearest_proposal_raw"]
    proposals = associated[0].get("proposals_raw")
    if not isinstance(proposals, list) or len(proposals) != 1 or proposals[0] != proposal:
        return unavailable("MULTIPLE_OR_INCONSISTENT_LAYOUT_PROPOSALS")
    if type(review.get("page")) is not int or associated[0].get("page") != review["page"]:
        return unavailable("REVIEWED_PANEL_PAGE_DOES_NOT_MATCH")
    reviewed_detections = {
        "caption_detection": associated[0].get("caption_detection"),
        "number_detection": proposal.get("number_detection") if isinstance(proposal, dict) else None,
        "unit_detection": proposal.get("unit_detection") if isinstance(proposal, dict) else None,
    }
    if any(type(review.get(name)) is not int or review[name] != actual
           for name, actual in reviewed_detections.items()):
        return unavailable("REVIEWED_DETECTIONS_DO_NOT_MATCH")
    if annual[0].get("unit_raw") != "kWh":
        return unavailable("EXPLICIT_KWH_UNIT_REQUIRED")
    if not isinstance(proposal, dict) or proposal.get("value_raw") != annual[0].get("value_raw"):
        return unavailable("TEXT_AND_LAYOUT_CANDIDATES_DO_NOT_UNIQUELY_AGREE")
    raw_value = annual[0].get("value_raw")
    try:
        amount = float(raw_value)
    except (TypeError, ValueError):
        return unavailable("UNSUPPORTED_ANNUAL_NUMBER_ENCODING")
    if not math.isfinite(amount) or amount < 0:
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

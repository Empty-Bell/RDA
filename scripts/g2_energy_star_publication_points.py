"""Three independent Samsung publication observations; this module has no rule output."""

import re
from typing import Any

from claim_recon import badge_attribution

PRESENT = "PRESENT"
ABSENT = "ABSENT"
UNKNOWN = "UNKNOWN"


def _point(state: str, evidence: list[dict[str, Any]], reason: str) -> dict[str, Any]:
    return {"state": state, "evidence": evidence, "reason": reason}


def _logo(candidate: dict[str, Any]) -> bool:
    """Only an image asset is a logo; text and raw flags are not logo evidence."""
    return candidate.get("tag") == "IMG" and bool(
        re.search(r"energy[\s_-]*star", str(candidate.get("src") or ""), re.I)
    )


def plp_logo_point(cards: list[dict[str, Any]], exact_sku: str) -> dict[str, Any]:
    matches = [card for card in cards if card.get("sku") == exact_sku]
    if len(matches) != 1:
        return _point(UNKNOWN, [], "Exact SKU card is missing or ambiguous on the observed PLP")
    card = matches[0]
    logos = [candidate for candidate in card.get("energy_candidates", []) if _logo(candidate)]
    if logos:
        return _point(PRESENT, logos, "Energy Star image observed inside the exact SKU PLP card")
    if (card.get("card_scope_contract") == "PLP_EXACT_LIST_ITEM_V2"
            and card.get("logo_inspection") == "SUPPORTED_EXACT_CARD_COMPLETE"
            and card.get("exact_sku_anchor_count") == 1
            and card.get("exact_sku_anchor_values") == [exact_sku]):
        return _point(ABSENT, [], "Exact SKU PLP card was completely inspected and has no Energy Star image")
    return _point(UNKNOWN, [], "PLP exact-SKU card boundary was not supported")


def pdp_logo_point(snapshot: dict[str, Any], exact_sku: str, identity_state: str) -> dict[str, Any]:
    if identity_state != "VERIFIED_EXACT_IDENTITY":
        return _point(UNKNOWN, [], "PDP exact identity is not verified")
    jsonld = [
        record for record in snapshot.get("product_jsonld", [])
        if record.get("sku") == exact_sku and record.get("mpn") in (None, exact_sku)
    ]
    logos = badge_attribution(snapshot, jsonld, exact_sku)
    if logos:
        return _point(PRESENT, logos, "Energy Star image attributed to the exact PDP primary surface")
    if snapshot.get("primary_logo_inspection") == "SUPPORTED_PRIMARY_SURFACE_COMPLETE" and len(jsonld) == 1:
        return _point(ABSENT, [], "Exact PDP primary surface was completely inspected and has no attributed Energy Star image")
    return _point(UNKNOWN, [], "PDP logo surface is unsupported, ambiguous, or lacks exact JSON-LD")


def spec_certification_point(snapshot: dict[str, Any], exact_sku: str, identity_state: str) -> dict[str, Any]:
    if identity_state != "VERIFIED_EXACT_IDENTITY":
        return _point(UNKNOWN, [], "PDP exact identity is not verified")
    affirmative = []
    for row in snapshot.get("visible_spec_energy_star_rows", []):
        text = str(row.get("text") or "")
        if re.search(r"energy[\s_-]*star", text, re.I) and re.search(
            r"certified|qualified|yes", text, re.I
        ):
            affirmative.append(row)
    if affirmative:
        return _point(PRESENT, affirmative, "Affirmative Energy Star certification text observed in a visible PDP Spec row")
    if snapshot.get("spec_surface_inspection") == "SUPPORTED_VISIBLE_SPEC_TABLE_COMPLETE":
        return _point(ABSENT, [], "Complete visible PDP Spec table was inspected and has no affirmative Energy Star certification row")
    return _point(UNKNOWN, [], "PDP Spec table was not mounted or its row schema is unsupported")


def collect_publication_points(
    cards: list[dict[str, Any]], samples: list[dict[str, Any]], snapshots: dict[str, dict[str, Any]],
    source_declarations: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source_declarations = source_declarations or {}
    records = []
    for sample in samples:
        sku = sample["exact_sku"]
        declaration = source_declarations.get(sku, {})
        if not isinstance(declaration, dict):
            raise ValueError("Publication source declaration must be keyed by exact SKU")
        snapshot = snapshots.get(sku)
        if not isinstance(snapshot, dict):
            unknown = _point(UNKNOWN, [], "No PDP visual snapshot was captured")
            records.append({"exact_sku": sku, "source_declarations_raw": declaration,
                            "plp_logo": plp_logo_point(cards, sku), "pdp_logo": unknown, "pdp_spec_certification": unknown})
            continue
        records.append({
            "exact_sku": sku,
            "source_declarations_raw": declaration,
            "plp_logo": plp_logo_point(cards, sku),
            "pdp_logo": pdp_logo_point(snapshot, sku, sample.get("status", "FAILED")),
            "pdp_spec_certification": spec_certification_point(snapshot, sku, sample.get("status", "FAILED")),
        })
    states = {state: 0 for state in (PRESENT, ABSENT, UNKNOWN)}
    for record in records:
        for name in ("plp_logo", "pdp_logo", "pdp_spec_certification"):
            states[record[name]["state"]] += 1
    return {"scope": "three independent observed Samsung publication points plus separate raw source declarations; no rule evaluation", "records": records, "states": states}

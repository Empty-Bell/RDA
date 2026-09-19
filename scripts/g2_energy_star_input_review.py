"""Prepare one non-assessing Energy Star input record per exact SKU."""

from collections import Counter
from typing import Any


def build_input_review(declarations: list[dict[str, Any]], binding: dict[str, Any]) -> dict[str, Any]:
    """Join source declarations to same-run EPA candidate evidence without a rule."""
    if binding.get("contract") != "G2_SAME_RUN_ENERGY_STAR_DECLARATION_CURRENT_INDEX_BINDING_V1":
        raise ValueError("Current Index binding contract is unavailable")
    candidates = binding.get("records")
    if not isinstance(declarations, list) or not isinstance(candidates, list):
        raise ValueError("Energy Star input review records are unavailable")
    declaration_by_sku = {item.get("exact_sku"): item for item in declarations}
    candidate_by_sku = {item.get("exact_sku", {}).get("exact_sku_raw"): item for item in candidates}
    if None in declaration_by_sku or len(declaration_by_sku) != len(declarations):
        raise ValueError("Energy Star declarations have duplicate or invalid exact SKU")
    if set(declaration_by_sku) != set(candidate_by_sku):
        raise ValueError("Energy Star declarations and Current Index binding SKU sets differ")
    records = []
    flag_pairs = Counter()
    candidate_states = Counter()
    for sku in sorted(declaration_by_sku):
        declaration, candidate = declaration_by_sku[sku], candidate_by_sku[sku]
        if candidate.get("current_certification_state") != "NOT_EVALUATED" or candidate.get("assessment") != "NOT_EVALUATED":
            raise ValueError("Input review cannot accept evaluated Current Index candidates")
        plp_flag = declaration.get("plp_energy_star_flag_raw")
        pdp_flag = declaration.get("pdp_energy_star_flag_raw")
        pair = f"plp={plp_flag!r};pdp={pdp_flag!r}"
        flag_pairs[pair] += 1
        candidate_states[candidate.get("candidate_projection_state")] += 1
        records.append({
            "exact_sku": sku,
            "plp_logo_source": {"field": "energyStarFlg", "raw_value": plp_flag},
            "pdp_logo_source": {"field": "energyStarFlag", "raw_value": pdp_flag},
            "pdp_spec_certification_source": {
                "field": "Bridge Specs ENERGY STAR rows",
                "raw_rows": declaration.get("pdp_energy_star_spec_rows_raw"),
            },
            "epa_current_index_candidate": candidate,
            "current_certification_state": "NOT_EVALUATED",
            "assessment": "NOT_EVALUATED",
        })
    return {
        "contract": "G2_ENERGY_STAR_THREE_POINT_INPUT_REVIEW_ONLY_V1",
        "source_run_id": binding.get("source_run_id"),
        "scope": "Exact-SKU PLP PF, PDP Next, Bridge Specs and same-run EPA candidate inputs; no publication or certification decision",
        "counts": {"exact_skus": len(records), "plp_pdp_raw_flag_pairs": dict(sorted(flag_pairs.items())),
                   "epa_candidate_states": dict(sorted(candidate_states.items()))},
        "records": records,
    }

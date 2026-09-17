"""Bind a verified refrigerator target to a provenance-checked EPA pattern.

The output is candidate evidence only. It never selects certification status or
creates an assessment.
"""

from g2_epa_wildcard_capture import positional_diagnostic
from g2_current_index_candidate_projection import project_candidates
from g2_samsung_suffix import normalize_terminal_aa

FOUR_KEYS = ("pd_id", "brand_name", "model_number", "energy_star_model_identifier")
REFRIGERATOR_CATEGORY = "Consumer Refrigeration Products"


def build_refrigerator_target_feed(pdp_results: list[dict], execution_id: str) -> dict:
    if not isinstance(execution_id, str) or not execution_id:
        raise ValueError("Refrigerator target execution ID invalid")
    targets = []
    for result in pdp_results:
        if result.get("status") != "VERIFIED_EXACT_IDENTITY":
            continue
        sku = result.get("exact_sku")
        bridge = result.get("bridge", {})
        if not isinstance(sku, str) or not sku or not bridge.get("sha256") or not bridge.get("url"):
            raise ValueError("Verified PDP result lacks target provenance")
        targets.append(
            {
                "exact_sku": sku,
                "pdp_identity_state": "VERIFIED_EXACT_IDENTITY",
                "source_run_id": execution_id,
                "source_evidence_refs": {
                    "bridge_url": bridge["url"],
                    "bridge_sha256": bridge["sha256"],
                },
            }
        )
    if len({target["exact_sku"] for target in targets}) != len(targets):
        raise ValueError("Verified PDP target SKU duplicated")
    return {
        "contract": "G2_SAME_RUN_REFRIGERATOR_TARGET_FEED_ONLY_V1",
        "source_run_id": execution_id,
        "targets": targets,
        "assessment": "NOT_EVALUATED",
    }


def refrigerator_current_index_rows(
    rows_with_sources: list[tuple[dict, dict]],
) -> list[tuple[dict, dict]]:
    """Select the literal category observed in Current Model Index raw rows."""
    if any(
        "product_category" not in row or "product_type" not in row for row, _ in rows_with_sources
    ):
        raise ValueError("Current Index refrigerator category/type fields unavailable")
    return [
        (row, source)
        for row, source in rows_with_sources
        if row["product_category"] == REFRIGERATOR_CATEGORY
    ]


def project_same_run_refrigerator_candidates(
    pdp_results: list[dict],
    scan: dict,
    rows_with_sources: list[tuple[dict, dict]],
    execution_id: str,
) -> dict:
    """Join only same-run verified refrigerator PDP targets to the full EPA scan."""
    feed = build_refrigerator_target_feed(pdp_results, execution_id)
    if scan.get("source_run_id") != execution_id:
        raise ValueError("Current Index scan execution provenance differs")
    candidates = project_candidates(
        scan, refrigerator_current_index_rows(rows_with_sources), feed["targets"]
    )
    return {"target_feed": feed, "candidate_projection": candidates}


def bridge_pattern_candidate(
    target: dict,
    current_index_row: dict,
    refrigerator_rows: list[dict],
    *,
    execution_id: str,
    refrigerator_metadata_sha256: str,
) -> dict:
    """Apply the approved positional diagnostic only after exact EPA row binding."""
    if target.get("pdp_identity_state") != "VERIFIED_EXACT_IDENTITY":
        raise ValueError("Pattern target lacks verified PDP identity")
    if target.get("source_run_id") != execution_id:
        raise ValueError("Pattern target execution provenance differs")
    if not isinstance(refrigerator_rows, list) or len(refrigerator_rows) != 1:
        raise ValueError("Refrigerator PD_ID query missing or ambiguous")
    refrigerator_row = refrigerator_rows[0]
    if any(not current_index_row.get(key) or not refrigerator_row.get(key) for key in FOUR_KEYS):
        raise ValueError("EPA four-key binding unavailable")
    if any(current_index_row[key] != refrigerator_row[key] for key in FOUR_KEYS):
        raise ValueError("EPA four-key binding mismatch")
    normalized = normalize_terminal_aa(target["exact_sku"])
    diagnostic = positional_diagnostic(
        current_index_row["model_number"],
        normalized["normalized_identifier"],
        dataset_id="p5st-her9",
        metadata_sha256=refrigerator_metadata_sha256,
    )
    return {
        "contract": "G2_P5ST_FOUR_KEY_PATTERN_CANDIDATE_ONLY_V1",
        "exact_sku": target["exact_sku"],
        "normalized_identifier": normalized,
        "epa_four_key": {key: current_index_row[key] for key in FOUR_KEYS},
        "pattern_diagnostic": diagnostic,
        "pattern_candidate_state": (
            "PROVENANCE_BOUND_POSITIONAL_CANDIDATE"
            if diagnostic["diagnostic"] == "POSITIONAL_COMPATIBLE_DIAGNOSTIC_ONLY"
            else "NOT_A_POSITIONAL_CANDIDATE"
        ),
        "current_certification_state": "NOT_EVALUATED",
        "assessment": "NOT_EVALUATED",
    }

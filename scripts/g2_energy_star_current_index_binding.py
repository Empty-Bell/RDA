"""Bind exact-SKU Energy Star declarations to a same-run EPA Current Index scan.

The binding supports literal comparison and the approved fixed-position model
pattern form. It emits candidate evidence only, never an audit outcome.
"""

from pathlib import Path

from g2_current_index_candidate_projection import candidate_reference, load_replayed_rows
from g2_samsung_suffix import normalize_terminal_aa

REFRIGERATOR_CATEGORY = "Consumer Refrigeration Products"


def _refrigerator_rows(rows_with_sources: list[tuple[dict, dict]]) -> list[tuple[dict, dict]]:
    if any("product_category" not in row or "product_type" not in row for row, _ in rows_with_sources):
        raise ValueError("Current Index refrigerator category/type fields unavailable")
    return [
        (row, source) for row, source in rows_with_sources
        if row["product_category"] == REFRIGERATOR_CATEGORY
    ]


def _identifiers(exact_sku: str) -> dict:
    if not isinstance(exact_sku, str) or not exact_sku:
        raise ValueError("Energy Star declaration exact SKU invalid")
    result = {"exact_sku_raw": exact_sku, "approved_normalized_identifier": None,
              "normalization": "NOT_APPLIED"}
    try:
        normalized = normalize_terminal_aa(exact_sku)
    except ValueError:
        return result
    result["approved_normalized_identifier"] = normalized["normalized_identifier"]
    result["normalization"] = normalized
    return result


def _pattern_compatibility(pattern: str, identifier: str) -> bool | None:
    """Compare one Current Index pattern positionally; None means unsupported."""
    if not isinstance(pattern, str) or not isinstance(identifier, str):
        return None
    if not pattern or not identifier:
        return None
    if any(not ("A" <= char <= "Z" or "0" <= char <= "9" or char in "*#") for char in pattern):
        return None
    if any(not ("A" <= char <= "Z" or "0" <= char <= "9") for char in identifier):
        return None
    if len(pattern) != len(identifier):
        return False
    for expected, actual in zip(pattern, identifier):
        if expected == "*":
            if not "A" <= actual <= "Z":
                return False
        elif expected == "#":
            if not "0" <= actual <= "9":
                return False
        elif expected != actual:
            return False
    return True


def bind_current_index(declaration_manifest: dict, capture_dir: Path) -> dict:
    """Attach same-run Current Index literal/pattern candidate references per SKU."""
    if declaration_manifest.get("status") != "PASS":
        raise ValueError("Energy Star declaration capture did not pass")
    run_id = declaration_manifest.get("run_id")
    declarations = declaration_manifest.get("declarations")
    if not isinstance(run_id, str) or not run_id or not isinstance(declarations, list):
        raise ValueError("Energy Star declaration provenance missing")
    if len({item.get("exact_sku") for item in declarations}) != len(declarations):
        raise ValueError("Energy Star declaration exact SKU duplicated")

    scan, rows_with_sources = load_replayed_rows(capture_dir)
    if scan.get("source_run_id") != run_id:
        raise ValueError("Current Index and Energy Star declaration runs differ")
    if (scan.get("query_completeness") != "COMPLETE_OBSERVED_QUERY"
            or scan.get("current_certification_state") != "NOT_EVALUATED"
            or scan.get("assessment") != "NOT_EVALUATED"):
        raise ValueError("Current Index scan is not candidate-only complete evidence")
    rows = _refrigerator_rows(rows_with_sources)
    references = [(row, candidate_reference(row, source)) for row, source in rows]
    output = []
    for declaration in sorted(declarations, key=lambda item: item["exact_sku"]):
        identifiers = _identifiers(declaration["exact_sku"])
        raw = identifiers["exact_sku_raw"]
        normalized = identifiers["approved_normalized_identifier"]
        raw_matches = [reference for row, reference in references if row["model_number"] == raw]
        normalized_matches = [
            reference for row, reference in references
            if normalized and normalized != raw and row["model_number"] == normalized
        ]
        positional_patterns, unsupported_patterns = [], []
        for row, reference in references:
            if "*" not in row["model_number"] and "#" not in row["model_number"]:
                continue
            compatibility = _pattern_compatibility(row["model_number"], normalized or "")
            if compatibility is True:
                positional_patterns.append(reference)
            elif compatibility is None:
                unsupported_patterns.append(reference)
        if raw_matches:
            state = "MATCHED_RAW_LITERAL_CANDIDATES"
        elif normalized_matches:
            state = "MATCHED_APPROVED_NORMALIZED_LITERAL_CANDIDATES"
        elif positional_patterns:
            state = "MATCHED_CURRENT_INDEX_POSITIONAL_PATTERN_CANDIDATES"
        elif unsupported_patterns:
            state = "UNRESOLVED_PATTERN_ENCODINGS_PRESENT"
        else:
            state = "COMPLETE_NO_LITERAL_OR_PATTERN_CANDIDATE"
        output.append({
            "exact_sku": identifiers,
            "source_declaration": {key: declaration.get(key) for key in (
                "source_family_id", "representative_sku", "sku_role",
                "plp_energy_star_flag_raw", "pdp_energy_star_flag_raw",
                "pdp_energy_star_spec_rows_raw",
            )},
            "candidate_projection_state": state,
            "raw_literal_candidates": raw_matches,
            "approved_normalized_literal_candidates": normalized_matches,
            "current_index_pattern_candidates": positional_patterns,
            "unsupported_pattern_references": unsupported_patterns,
            "current_certification_state": "NOT_EVALUATED",
            "assessment": "NOT_EVALUATED",
        })
    return {
            "contract": "G2_SAME_RUN_ENERGY_STAR_DECLARATION_CURRENT_INDEX_BINDING_V2",
        "source_run_id": run_id,
        "scan_query_completeness": scan["query_completeness"],
        "records": output,
    }

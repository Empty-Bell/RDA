"""Project exact Samsung SKU candidates from a replayed Current Model Index scan.

This module only reports candidate evidence.  It does not choose a certification
winner, infer absence from an unresolved pattern, or evaluate publication rules.
"""

import argparse
import json
from pathlib import Path

from g2_epa_current_index_samsung_capture import page_rows, replay_capture
from g2_samsung_suffix import normalize_terminal_aa

REQUIRED_TARGET_FIELDS = {"exact_sku", "pdp_identity_state", "source_run_id"}
REQUIRED_ROW_FIELDS = {
    "source_row_id",
    "pd_id",
    "brand_name",
    "model_number",
    "energy_star_model_identifier",
}


def target_identifiers(target: dict) -> dict:
    if not REQUIRED_TARGET_FIELDS <= set(target):
        raise ValueError("Current Index target provenance missing")
    if target["pdp_identity_state"] != "VERIFIED_EXACT_IDENTITY":
        raise ValueError("Current Index target lacks verified PDP identity")
    exact_sku = target["exact_sku"]
    if not isinstance(exact_sku, str) or not exact_sku:
        raise ValueError("Current Index exact SKU invalid")
    identifiers = {"exact_sku_raw": exact_sku, "raw_identifier": exact_sku}
    try:
        suffix = normalize_terminal_aa(exact_sku)
    except ValueError:
        identifiers["approved_normalized_identifier"] = None
        identifiers["normalization"] = "NOT_APPLIED"
    else:
        identifiers["approved_normalized_identifier"] = suffix["normalized_identifier"]
        identifiers["normalization"] = suffix
    return identifiers


def candidate_reference(row: dict, source: dict) -> dict:
    if not REQUIRED_ROW_FIELDS <= set(row) or any(not row[field] for field in REQUIRED_ROW_FIELDS):
        raise ValueError("Current Index candidate row identity invalid")
    return {
        "source_record_name": source["name"],
        "source_body_sha256": source["body_sha256"],
        "source_row_id": row["source_row_id"],
        "pd_id": row["pd_id"],
        "brand_name": row["brand_name"],
        "model_number_raw": row["model_number"],
        "energy_star_model_identifier": row["energy_star_model_identifier"],
    }


def project_candidates(
    scan: dict, rows_with_sources: list[tuple[dict, dict]], targets: list[dict]
) -> dict:
    if (
        scan.get("query_completeness") != "COMPLETE_OBSERVED_QUERY"
        or scan.get("current_certification_state") != "NOT_EVALUATED"
        or scan.get("assessment") != "NOT_EVALUATED"
    ):
        raise ValueError("Current Index scan is not a complete candidate-only source")
    if len({target.get("exact_sku") for target in targets}) != len(targets):
        raise ValueError("Current Index target SKU duplicated")
    all_rows = []
    for row, source in rows_with_sources:
        if row.get("brand_name", "").upper() != "SAMSUNG":
            raise ValueError("Current Index non-Samsung row supplied")
        all_rows.append((row, source, candidate_reference(row, source)))
    records = []
    for target in targets:
        identifiers = target_identifiers(target)
        if target["source_run_id"] != scan["source_run_id"]:
            raise ValueError("Current Index target and scan run provenance differ")
        raw = identifiers["raw_identifier"]
        normalized = identifiers["approved_normalized_identifier"]
        raw_matches = [reference for row, _, reference in all_rows if row["model_number"] == raw]
        normalized_matches = [
            reference
            for row, _, reference in all_rows
            if normalized and normalized != raw and row["model_number"] == normalized
        ]
        pattern_references = [
            reference
            for row, _, reference in all_rows
            if "*" in row["model_number"] or "#" in row["model_number"]
        ]
        if raw_matches:
            state = "MATCHED_RAW_LITERAL_CANDIDATES"
        elif normalized_matches:
            state = "MATCHED_APPROVED_NORMALIZED_LITERAL_CANDIDATES"
        elif pattern_references:
            state = "UNRESOLVED_PATTERN_ENCODINGS_PRESENT"
        else:
            state = "COMPLETE_NO_LITERAL_OR_PATTERN_CANDIDATE"
        records.append(
            {
                "exact_sku": identifiers,
                "target_source_evidence_ids": target.get("source_evidence_ids", []),
                "candidate_projection_state": state,
                "raw_literal_candidates": raw_matches,
                "approved_normalized_literal_candidates": normalized_matches,
                "unresolved_pattern_references": pattern_references,
                "current_certification_state": "NOT_EVALUATED",
                "assessment": "NOT_EVALUATED",
            }
        )
    return {
        "contract": "G2_CURRENT_INDEX_EXACT_TARGET_CANDIDATE_PROJECTION_ONLY_V1",
        "source_run_id": scan["source_run_id"],
        "scan_query_completeness": scan["query_completeness"],
        "records": records,
    }


def load_replayed_rows(capture_dir: Path) -> tuple[dict, list[tuple[dict, dict]]]:
    manifest = replay_capture(capture_dir)
    sources = {record["name"]: record for record in manifest["sources"]}
    rows_with_sources = []
    for name in sorted(sources):
        if name.startswith("page-"):
            for row in page_rows((capture_dir / sources[name]["file"]).read_bytes()):
                rows_with_sources.append((row, sources[name]))
    scan = {**manifest["scan"], "source_run_id": manifest["run_id"]}
    return scan, rows_with_sources


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-dir", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    scan, rows = load_replayed_rows(args.capture_dir)
    targets = json.loads(args.targets.read_text(encoding="utf-8"))
    if not isinstance(targets, list):
        raise ValueError("Current Index targets must be an array")
    result = project_candidates(scan, rows, targets)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "targets": len(result["records"])}))


if __name__ == "__main__":
    main()

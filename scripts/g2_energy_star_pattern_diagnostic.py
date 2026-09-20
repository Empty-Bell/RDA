"""Bind Energy Star declaration candidates to reviewed p5st pattern evidence.

This collector records only a source-bound positional candidate.  It does not
select current certification, infer EPA registration, or issue an audit result.
"""

import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from epa_queries import decode_rows, query_url
from g2_epa_wildcard_capture import positional_diagnostic, project_source
from g2_refrigerator_pattern_bridge import FOUR_KEYS
from g2_refrigerator_pattern_capture import DATASET, METADATA_URL, USER_AGENT, validate_refrigerator_row


def compatible_pattern_pairs(binding: dict, metadata_sha256: str) -> list[dict]:
    """Keep only declarations whose normalized SKU fits a Current Index pattern.

    This is a fetch filter only.  The reported candidate is produced later, only
    after the corresponding p5st row passes the four-key provenance check.
    """
    if binding.get("contract") != "G2_SAME_RUN_ENERGY_STAR_DECLARATION_CURRENT_INDEX_BINDING_V1":
        raise ValueError("Energy Star Current Index binding contract unavailable")
    pairs = []
    for record in binding.get("records", []):
        identifiers = record.get("exact_sku", {})
        exact_sku = identifiers.get("exact_sku_raw")
        normalized = identifiers.get("approved_normalized_identifier")
        if not isinstance(exact_sku, str) or not exact_sku:
            raise ValueError("Energy Star pattern declaration exact SKU invalid")
        if not isinstance(normalized, str) or not normalized:
            continue
        for reference in record.get("unresolved_pattern_references", []):
            diagnostic = positional_diagnostic(
                reference.get("model_number_raw"),
                normalized,
                dataset_id=DATASET,
                metadata_sha256=metadata_sha256,
            )
            if diagnostic["diagnostic"] == "POSITIONAL_COMPATIBLE_DIAGNOSTIC_ONLY":
                pairs.append(
                    {
                        "exact_sku": exact_sku,
                        "normalized_identifier": identifiers,
                        "current_index_reference": reference,
                    }
                )
    return pairs


def _four_key_row(reference: dict) -> dict:
    row = {
        "pd_id": reference.get("pd_id"),
        "brand_name": reference.get("brand_name"),
        "model_number": reference.get("model_number_raw"),
        "energy_star_model_identifier": reference.get("energy_star_model_identifier"),
    }
    if any(not row[key] for key in FOUR_KEYS):
        raise ValueError("Energy Star pattern Current Index four-key unavailable")
    return row


def bridge_pattern_candidate(pair: dict, refrigerator_row: dict, metadata_sha256: str) -> dict:
    """Return one candidate only when Current Index and p5st rows agree exactly."""
    current = _four_key_row(pair["current_index_reference"])
    if any(not refrigerator_row.get(key) for key in FOUR_KEYS):
        raise ValueError("Energy Star p5st four-key unavailable")
    if any(str(current[key]) != str(refrigerator_row[key]) for key in FOUR_KEYS):
        raise ValueError("Energy Star p5st four-key mismatch")
    normalized = pair["normalized_identifier"]
    diagnostic = positional_diagnostic(
        refrigerator_row["model_number"],
        normalized["approved_normalized_identifier"],
        dataset_id=DATASET,
        metadata_sha256=metadata_sha256,
    )
    if diagnostic["diagnostic"] != "POSITIONAL_COMPATIBLE_DIAGNOSTIC_ONLY":
        raise ValueError("Energy Star p5st row is no longer positionally compatible")
    return {
        "contract": "G2_ENERGY_STAR_P5ST_FOUR_KEY_PATTERN_CANDIDATE_ONLY_V1",
        "exact_sku": pair["exact_sku"],
        "normalized_identifier": normalized,
        "current_index_reference": pair["current_index_reference"],
        "epa_four_key": {key: current[key] for key in FOUR_KEYS},
        "pattern_diagnostic": diagnostic,
        "pattern_candidate_state": "PROVENANCE_BOUND_POSITIONAL_CANDIDATE",
        "current_certification_state": "NOT_EVALUATED",
        "assessment": "NOT_EVALUATED",
    }


def capture_pattern_candidates(out: Path, binding: dict, *, execution_id: str) -> dict:
    """Capture reviewed p5st rows for same-run compatible declaration candidates."""
    if binding.get("source_run_id") != execution_id:
        raise ValueError("Energy Star pattern and Current Index execution provenance differs")
    out.mkdir(parents=True, exist_ok=False)
    sources = []

    def fetch(name: str, url: str) -> bytes:
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
        )
        try:
            response = urllib.request.urlopen(request, timeout=45)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body, status = response.read(), response.status
            content_type = response.headers.get("Content-Type", "")
        filename = name + ".bin"
        (out / filename).write_bytes(body)
        if status != 200 or "json" not in content_type.lower() or not body:
            raise ValueError("Energy Star p5st source unavailable: " + name)
        sources.append({
            "name": name, "file": filename, "url": url, "status": status,
            "content_type": content_type, "body_sha256": hashlib.sha256(body).hexdigest(),
        })
        return body

    metadata_body = fetch("metadata", METADATA_URL)
    project_source("refrigerator-metadata", metadata_body)
    metadata_sha256 = hashlib.sha256(metadata_body).hexdigest()
    pairs = compatible_pattern_pairs(binding, metadata_sha256)
    rows_by_pd_id = {}
    for pd_id in sorted({str(item["current_index_reference"].get("pd_id")) for item in pairs}):
        if not re.fullmatch(r"\d+", pd_id):
            raise ValueError("Energy Star compatible pattern PD_ID invalid")
        body = fetch("pd-id-" + pd_id, query_url(DATASET, {"$where": "pd_id = " + pd_id, "$limit": 2}))
        rows_by_pd_id[pd_id] = validate_refrigerator_row(pd_id, decode_rows(200, "application/json", body))
    candidates = [
        bridge_pattern_candidate(item, rows_by_pd_id[str(item["current_index_reference"]["pd_id"])], metadata_sha256)
        for item in pairs
    ]
    candidates_by_sku = {}
    for candidate in candidates:
        candidates_by_sku.setdefault(candidate["exact_sku"], []).append(candidate)
    record_skus = [item.get("exact_sku", {}).get("exact_sku_raw") for item in binding.get("records", [])]
    if None in record_skus or len(set(record_skus)) != len(record_skus):
        raise ValueError("Energy Star pattern binding exact SKU coverage invalid")
    result = {
        "contract": "G2_ENERGY_STAR_SAME_RUN_P5ST_PATTERN_DIAGNOSTIC_ONLY_V1",
        "source_run_id": execution_id,
        "scope": "Exact-SKU source declarations and same-run Current Index patterns; p5st four-key candidate diagnostic only",
        "sources": sources,
        "counts": {
            "exact_skus": len(record_skus),
            "compatible_pattern_pairs": len(pairs),
            "provenance_bound_pattern_candidates": len(candidates),
        },
        "records": [
            {"exact_sku": sku, "pattern_candidates": candidates_by_sku.get(sku, []),
             "current_certification_state": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"}
            for sku in sorted(record_skus)
        ],
        "current_certification_state": "NOT_EVALUATED",
        "assessment": "NOT_EVALUATED",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result

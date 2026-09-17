"""Capture same-run p5st rows only for compatible Current Index pattern candidates."""

import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from epa_queries import decode_rows, query_url
from g2_epa_wildcard_capture import positional_diagnostic, project_source
from g2_refrigerator_pattern_bridge import bridge_pattern_candidate

DATASET = "p5st-her9"
METADATA_URL = "https://data.energystar.gov/api/views/p5st-her9.json"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def compatible_pattern_pairs(
    target_feed: dict, candidate_projection: dict, metadata_sha256: str
) -> list[dict]:
    targets = {target["exact_sku"]: target for target in target_feed["targets"]}
    pairs = []
    for record in candidate_projection["records"]:
        exact = record["exact_sku"]
        normalized = exact["approved_normalized_identifier"]
        if not normalized:
            continue
        target = targets.get(exact["exact_sku_raw"])
        if target is None:
            raise ValueError("Candidate projection target missing from same-run feed")
        for reference in record["unresolved_pattern_references"]:
            diagnostic = positional_diagnostic(
                reference["model_number_raw"],
                normalized,
                dataset_id=DATASET,
                metadata_sha256=metadata_sha256,
            )
            if diagnostic["diagnostic"] == "POSITIONAL_COMPATIBLE_DIAGNOSTIC_ONLY":
                pairs.append({"target": target, "current_index_reference": reference})
    return pairs


def validate_refrigerator_row(pd_id: str, rows: list[dict]) -> dict:
    if not re.fullmatch(r"\d+", pd_id) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("Compatible refrigerator PD_ID query missing or ambiguous")
    row = rows[0]
    if str(row.get("pd_id")) != pd_id:
        raise ValueError("Compatible refrigerator PD_ID query returned another row")
    return row


def capture_pattern_rows(
    out: Path,
    target_feed: dict,
    candidate_projection: dict,
    *,
    execution_id: str,
) -> dict:
    """Preserve raw p5st metadata and the exact rows needed for compatible patterns."""
    out.mkdir(parents=True, exist_ok=False)
    records = []

    def fetch(name: str, url: str) -> bytes:
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
        )
        try:
            response = urllib.request.urlopen(request, timeout=45)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
        filename = name + ".bin"
        (out / filename).write_bytes(body)
        if status != 200 or "json" not in content_type.lower() or not body:
            raise ValueError("Refrigerator pattern source unavailable: " + name)
        records.append(
            {
                "name": name,
                "file": filename,
                "url": url,
                "status": status,
                "content_type": content_type,
                "body_sha256": hashlib.sha256(body).hexdigest(),
            }
        )
        return body

    metadata_body = fetch("metadata", METADATA_URL)
    project_source("refrigerator-metadata", metadata_body)
    metadata_sha256 = hashlib.sha256(metadata_body).hexdigest()
    pairs = compatible_pattern_pairs(target_feed, candidate_projection, metadata_sha256)
    rows_by_pd_id = {}
    for pd_id in sorted({str(pair["current_index_reference"]["pd_id"]) for pair in pairs}):
        body = fetch(
            "pd-id-" + pd_id,
            query_url(DATASET, {"$where": "pd_id = " + pd_id, "$limit": 2}),
        )
        rows_by_pd_id[pd_id] = validate_refrigerator_row(
            pd_id, decode_rows(200, "application/json", body)
        )
    bridges = []
    for pair in pairs:
        reference = pair["current_index_reference"]
        current_row = {
            "pd_id": reference["pd_id"],
            "brand_name": reference["brand_name"],
            "model_number": reference["model_number_raw"],
            "energy_star_model_identifier": reference["energy_star_model_identifier"],
        }
        bridges.append(
            bridge_pattern_candidate(
                pair["target"],
                current_row,
                [rows_by_pd_id[str(current_row["pd_id"])]],
                execution_id=execution_id,
                refrigerator_metadata_sha256=metadata_sha256,
            )
        )
    result = {
        "contract": "G2_SAME_RUN_P5ST_PATTERN_CAPTURE_AND_BRIDGE_ONLY_V1",
        "source_run_id": execution_id,
        "sources": records,
        "compatible_pattern_candidate_count": len(pairs),
        "bridges": bridges,
        "current_certification_state": "NOT_EVALUATED",
        "assessment": "NOT_EVALUATED",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result

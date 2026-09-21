"""Capture refrigerator numeric fields for Current Index candidate PD_IDs.

The Current Model Index remains the certification source.  This collector only
uses its already-matched PD_IDs to fetch annual energy and total capacity from
EPA's refrigerator family dataset for source comparison.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
from typing import Any
import zipfile


DATASET = "p5st-her9"
CONTRACT = "G2_EPA_REFRIGERATOR_NUMERIC_ENRICHMENT_V1"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
REQUIRED_FIELDS = {
    "pd_id",
    "brand_name",
    "model_number",
    "annual_energy_use_kwh_yr",
    "capacity_total_volume_ft3",
}
CANDIDATE_FIELDS = (
    "raw_literal_candidates",
    "approved_normalized_literal_candidates",
    "current_index_pattern_candidates",
)


def _one_json(archive: zipfile.ZipFile, suffix: str) -> dict[str, Any]:
    names = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise ValueError(f"Artifact must contain exactly one {suffix}")
    return json.loads(archive.read(names[0]))


def load_binding(artifact_zip: Path) -> dict[str, Any]:
    with zipfile.ZipFile(artifact_zip) as archive:
        binding = _one_json(archive, "/energy-star-source/current-index-binding.json")
    if binding.get("contract") != "G2_SAME_RUN_ENERGY_STAR_DECLARATION_CURRENT_INDEX_BINDING_V2":
        raise ValueError("Current Index binding contract is unsupported")
    if binding.get("scan_query_completeness") != "COMPLETE_OBSERVED_QUERY":
        raise ValueError("Current Index binding is incomplete")
    return binding


def candidate_ids(record: dict[str, Any]) -> list[str]:
    identifiers = []
    for field in CANDIDATE_FIELDS:
        candidates = record.get(field, [])
        if not isinstance(candidates, list):
            raise ValueError("Current Index candidate collection is invalid")
        for candidate in candidates:
            value = candidate.get("pd_id") if isinstance(candidate, dict) else None
            if not isinstance(value, str) or not value.isdigit():
                raise ValueError("Current Index candidate PD_ID is invalid")
            identifiers.append(value)
    return sorted(set(identifiers), key=int)


def metadata_projection(body: bytes) -> dict[str, Any]:
    data = json.loads(body)
    fields = sorted(
        column.get("fieldName")
        for column in data.get("columns", [])
        if isinstance(column, dict) and isinstance(column.get("fieldName"), str)
    )
    if data.get("id") != DATASET or not REQUIRED_FIELDS <= set(fields):
        raise ValueError("EPA refrigerator numeric schema is invalid")
    return {
        "id": data["id"],
        "rows_updated_at": data.get("rowsUpdatedAt"),
        "view_last_modified": data.get("viewLastModified"),
        "fields": fields,
    }


def decode_rows(body: bytes, requested_ids: set[str]) -> list[dict[str, Any]]:
    rows = json.loads(body)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("EPA refrigerator numeric response is not an array")
    seen = set()
    for row in rows:
        pd_id = row.get("pd_id")
        if row.get("brand_name", "").upper() != "SAMSUNG" or pd_id not in requested_ids:
            raise ValueError("EPA refrigerator numeric response escaped the requested scope")
        if pd_id in seen:
            raise ValueError("EPA refrigerator numeric response duplicated a PD_ID")
        seen.add(pd_id)
    return rows


def _numeric_value(row: dict[str, Any], field: str) -> float | None:
    value = row.get(field)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"EPA numeric field {field} is invalid") from None


def build_projection(binding: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["pd_id"]: row for row in rows}
    output = []
    for record in binding.get("records", []):
        exact_sku = record.get("exact_sku", {}).get("exact_sku_raw")
        if not isinstance(exact_sku, str) or not exact_sku:
            raise ValueError("Current Index binding exact SKU is invalid")
        ids = candidate_ids(record)
        matched = [by_id[value] for value in ids if value in by_id]
        missing = [value for value in ids if value not in by_id]
        fields = {}
        for source_field, output_field, unit in (
            ("annual_energy_use_kwh_yr", "annual_energy_kwh", "kWh/year"),
            ("capacity_total_volume_ft3", "capacity_cu_ft", "cu ft"),
        ):
            values = sorted({value for row in matched if (value := _numeric_value(row, source_field)) is not None})
            if not ids:
                state, amount = "NO_CURRENT_INDEX_CANDIDATE", None
            elif missing:
                state, amount = "PARTIAL_EPA_FAMILY_COVERAGE", None
            elif len(values) == 1 and len(matched) == len(ids):
                state, amount = "VALUE", values[0]
            elif not values:
                state, amount = "EPA_VALUE_MISSING", None
            else:
                state, amount = "CONFLICTING_EPA_VALUES", None
            fields[output_field] = {
                "state": state,
                "amount": amount,
                "unit": unit,
                "source_field": source_field,
                "observed_values": values,
            }
        output.append({
            "exact_sku": exact_sku,
            "current_index_pd_ids": ids,
            "matched_epa_pd_ids": [row["pd_id"] for row in matched],
            "missing_epa_pd_ids": missing,
            **fields,
        })
    return {
        "contract": CONTRACT,
        "status": "PASS",
        "source_run_id": binding.get("source_run_id"),
        "scope": {
            "certification_source": "EPA_CURRENT_MODEL_INDEX_8wj2-sec8",
            "numeric_enrichment_source": "EPA_REFRIGERATOR_FAMILY_p5st-her9",
            "join_key": "pd_id",
            "changes_certification_assessment": False,
        },
        "records": output,
        "assessment_enabled": False,
    }


def replay_capture_from_binding(binding: dict[str, Any], root: Path) -> dict[str, Any]:
    projection = json.loads((root / "projection.json").read_text(encoding="utf-8"))
    if projection.get("contract") != CONTRACT or projection.get("status") != "PASS":
        raise ValueError("EPA numeric projection contract is invalid")
    sources = {source["name"]: source for source in projection.get("sources", [])}
    if set(sources) != {"metadata-before", "rows", "metadata-after"}:
        raise ValueError("EPA numeric raw sources are incomplete")
    bodies = {}
    for name, source in sources.items():
        body = (root / source["file"]).read_bytes()
        if hashlib.sha256(body).hexdigest() != source.get("body_sha256"):
            raise ValueError("EPA numeric raw source hash does not replay")
        bodies[name] = body
    before = metadata_projection(bodies["metadata-before"])
    after = metadata_projection(bodies["metadata-after"])
    if before != after or before != projection.get("metadata"):
        raise ValueError("EPA numeric metadata does not replay")
    pd_ids = {value for record in binding["records"] for value in candidate_ids(record)}
    rebuilt = build_projection(binding, decode_rows(bodies["rows"], pd_ids))
    for key in ("contract", "status", "source_run_id", "scope", "records", "assessment_enabled"):
        if rebuilt[key] != projection.get(key):
            raise ValueError("EPA numeric projection does not replay")
    return projection


def replay_capture(artifact_zip: Path, root: Path) -> dict[str, Any]:
    return replay_capture_from_binding(load_binding(artifact_zip), root)


def query_url(pd_ids: list[str]) -> str:
    if not pd_ids:
        return ""
    params = {
        "$select": ",".join(sorted(REQUIRED_FIELDS)),
        "$where": "pd_id in (" + ",".join(pd_ids) + ")",
        "$order": "pd_id",
        "$limit": "1000",
    }
    return f"https://data.energystar.gov/resource/{DATASET}.json?" + urllib.parse.urlencode(params)


def capture_from_binding(binding: dict[str, Any], out: Path) -> dict[str, Any]:
    """Capture/replay numeric EPA evidence for one same-run Current Index binding."""
    if binding.get("contract") != "G2_SAME_RUN_ENERGY_STAR_DECLARATION_CURRENT_INDEX_BINDING_V2":
        raise ValueError("Current Index binding contract is unsupported")
    if binding.get("scan_query_completeness") != "COMPLETE_OBSERVED_QUERY":
        raise ValueError("Current Index binding is incomplete")
    out.mkdir(parents=True, exist_ok=True)
    pd_ids = sorted({value for record in binding["records"] for value in candidate_ids(record)}, key=int)
    if not pd_ids:
        raise ValueError("Current Index binding has no candidate PD_IDs")

    sources = []

    def fetch(name: str, url: str) -> bytes:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            response = urllib.request.urlopen(request, timeout=45)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
        if status != 200 or "json" not in content_type.lower() or not body:
            raise ValueError(f"EPA source unavailable: {name}")
        filename = name + ".json"
        (out / filename).write_bytes(body)
        sources.append({
            "name": name,
            "file": filename,
            "url": url,
            "status": status,
            "content_type": content_type,
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "size_bytes": len(body),
        })
        return body

    metadata_url = f"https://data.energystar.gov/api/views/{DATASET}.json"
    before = metadata_projection(fetch("metadata-before", metadata_url))
    rows = decode_rows(fetch("rows", query_url(pd_ids)), set(pd_ids))
    after = metadata_projection(fetch("metadata-after", metadata_url))
    if before != after:
        raise ValueError("EPA refrigerator numeric metadata changed during capture")
    projection = build_projection(binding, rows)
    projection["captured_at"] = datetime.now(timezone.utc).isoformat()
    projection["github_run_id"] = os.getenv("GITHUB_RUN_ID")
    projection["git_sha"] = os.getenv("GITHUB_SHA")
    projection["sources"] = sources
    projection["metadata"] = before
    (out / "projection.json").write_text(json.dumps(projection, indent=2) + "\n", encoding="utf-8")
    return projection


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    binding = load_binding(args.artifact_zip)
    capture_from_binding(binding, args.out)
    replay_capture(args.artifact_zip, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

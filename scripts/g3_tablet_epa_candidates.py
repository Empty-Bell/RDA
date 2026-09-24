"""Capture current EPA Computers rows and link only strict Tablet model candidates."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from source_contract import epa_contract, pdp_facts, project_computer_specs

DATASET = "rxdj-2c88"
BASE = f"https://data.energystar.gov/resource/{DATASET}.json"
META_URL = f"https://data.energystar.gov/api/views/{DATASET}.json"
BRAND_WHERE = "upper(brand_name) = 'SAMSUNG'"
COLLECTION_CONTRACT = "G3_TABLET_EXACT_SKU_PDP_V1"
CONTRACT = "G3_TABLET_EPA_SOURCE_CANDIDATES_V1"
PAGE_SIZE = 100


def _read_json(path):
    return json.loads(Path(path).read_bytes())


def _fetch(url):
    request = Request(url, headers={"User-Agent": "RDA-G3-Tablet-EPA-Source/1.0", "Accept": "application/json"})
    for attempt in range(5):
        try:
            with urlopen(request, timeout=45) as response:
                return response.read(), response.headers.get_content_type(), response.status
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 4:
                raise
        except URLError:
            if attempt == 4:
                raise
        time.sleep(min(2 ** attempt, 16))
    raise RuntimeError("EPA retry loop exhausted")


def _query(params):
    body, content_type, status = _fetch(BASE + "?" + urlencode(params))
    if status != 200 or "json" not in content_type.lower():
        raise ValueError("EPA Computers query was not successful JSON")
    rows = json.loads(body)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("EPA Computers query response is not an array of records")
    return rows


def capture_epa(output, page_size=PAGE_SIZE):
    """Capture the full current Samsung EPA source cohort with row/hash checks."""
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    raw_meta, content_type, status = _fetch(META_URL)
    if status != 200 or "json" not in content_type.lower():
        raise ValueError("EPA Computers metadata unavailable")
    metadata = json.loads(raw_meta)
    if metadata.get("id") != DATASET or metadata.get("name") != "ENERGY STAR Certified Computers V9.0":
        raise ValueError("EPA Computers dataset identity changed")
    counts = _query({"$select": "count(*) as row_count", "$where": BRAND_WHERE})
    if len(counts) != 1 or not str(counts[0].get("row_count", "")).isdigit():
        raise ValueError("EPA Samsung row count response malformed")
    expected = int(counts[0]["row_count"])
    if expected < 1 or expected > 10000 or page_size < 1 or page_size > 500:
        raise ValueError("EPA Samsung cohort or page size is outside the bounded capture range")
    columns = metadata.get("columns", [])
    available = {column.get("fieldName") for column in columns if isinstance(column, dict)}
    # Keep all current source fields when the metadata provides valid field names.
    field_names = [column.get("fieldName") for column in columns
        if isinstance(column, dict) and isinstance(column.get("fieldName"), str)
        and re.fullmatch(r"[a-z][a-z0-9_]*", column["fieldName"])]
    required = {"pd_id", "brand_name", "model_number", "markets", "type", "operating_system_name"}
    if not required <= available or not field_names:
        raise ValueError("EPA Computers metadata is missing required identity/context fields")
    select = ":id as source_row_id," + ",".join(field_names)
    rows, urls = [], []
    for offset in range(0, expected, page_size):
        params = {"$where": BRAND_WHERE, "$select": select, "$order": ":id",
            "$limit": str(page_size), "$offset": str(offset)}
        url = BASE + "?" + urlencode(params)
        page = _query(params)
        if not page:
            raise ValueError("EPA Samsung cohort ended before the count")
        rows.extend(page)
        urls.append(url)
    if len(rows) != expected or any(str(row.get("brand_name", "")).strip().upper() != "SAMSUNG" for row in rows):
        raise ValueError("EPA Samsung pages do not match the complete source count")
    row_ids = [row.get("source_row_id") for row in rows]
    if any(not value for value in row_ids) or len(set(row_ids)) != len(row_ids):
        raise ValueError("EPA Samsung rows have missing or duplicate source IDs")
    epa_contract(metadata, rows, dataset=DATASET)
    after = _query({"$select": "count(*) as row_count", "$where": BRAND_WHERE})
    meta_after_raw, after_type, after_status = _fetch(META_URL)
    meta_after = json.loads(meta_after_raw) if after_status == 200 and "json" in after_type.lower() else {}
    if (len(after) != 1 or int(after[0].get("row_count", -1)) != expected
            or meta_after.get("id") != DATASET
            or meta_after.get("rowsUpdatedAt") != metadata.get("rowsUpdatedAt")):
        raise ValueError("EPA source count/schema timestamp changed during capture")
    metadata_projection = {key: metadata.get(key) for key in
        ("id", "name", "rowsUpdatedAt", "viewLastModified", "publicationDate")}
    metadata_projection["columns"] = [{key: column.get(key) for key in
        ("fieldName", "name", "dataTypeName")} for column in columns
        if isinstance(column, dict) and not str(column.get("fieldName", "")).startswith(":")]
    meta_bytes = (json.dumps(metadata_projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    rows_bytes = (json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    (out / "metadata.json").write_bytes(meta_bytes)
    (out / "samsung-current-rows.json").write_bytes(rows_bytes)
    summary = {"contract": "G3_TABLET_EPA_CURRENT_SOURCE_V1", "dataset_id": DATASET,
        "capture_run_id": os.getenv("GITHUB_RUN_ID"), "captured_at": datetime.now(timezone.utc).isoformat(),
        "rows_updated_at": metadata.get("rowsUpdatedAt"), "row_count": len(rows),
        "brand_condition": BRAND_WHERE, "page_size": page_size, "row_page_urls": urls,
        "metadata_sha256": hashlib.sha256(meta_bytes).hexdigest(),
        "rows_sha256": hashlib.sha256(rows_bytes).hexdigest(), "status": "PASS",
        "completeness": "COUNT_MATCHED_PAGED_UNIQUE_SOURCE_IDS_STABLE_COUNT_AND_TIMESTAMP",
        "certification_matching": "NOT_EVALUATED"}
    (out / "capture-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata_projection, rows, summary


def load_collection(root, expected_run_id):
    """Verify every successful exact-SKU shard and its saved PDP/Specs evidence."""
    root = Path(root)
    dirs = sorted(path for path in root.glob("shard-*") if path.is_dir())
    summaries = [_read_json(path / "shard-summary.json") for path in dirs]
    if not summaries or any(row.get("contract") != COLLECTION_CONTRACT or row.get("status") != "PASS"
            or str(row.get("collection_run_id")) != str(expected_run_id) for row in summaries):
        raise ValueError("Tablet collection shards are incomplete or from the wrong run")
    shard_count = summaries[0].get("shard_count")
    shard_indexes = {row.get("shard_index") for row in summaries}
    if (type(shard_count) is not int or shard_count < 1 or len(summaries) != shard_count
            or shard_indexes != set(range(shard_count))
            or any(row.get("shard_count") != shard_count for row in summaries)):
        raise ValueError("Tablet collection shard identity/count is inconsistent")
    expected = set(summaries[0].get("all_population_skus", []))
    assigned = [sku for row in summaries for sku in row.get("assigned_skus", [])]
    if (not expected or len(assigned) != len(expected) or set(assigned) != expected
            or len(set(assigned)) != len(assigned)
            or any(set(row.get("all_population_skus", [])) != expected for row in summaries)):
        raise ValueError("Tablet shards do not cover the exact source population once")
    source_ids = {str(row.get("source_run_id")) for row in summaries}
    if len(source_ids) != 1:
        raise ValueError("Tablet shards do not share one source reconnaissance run")
    products, records, claims, facts = {}, {}, {}, {}
    for shard in dirs:
        for item in _read_json(shard / "products.json"):
            sku = item.get("exact_sku")
            if sku not in expected or sku in products:
                raise ValueError("Tablet source product is missing, duplicated, or outside population")
            products[sku] = item
        for result_path in sorted((shard / "pdp").glob("*/result.json")):
            result = _read_json(result_path)
            sku = result.get("exact_sku")
            selection = result.get("selection_identity")
            visible = result.get("selection_observed_raw")
            final_url = urlsplit(str(result.get("final_url") or ""))
            if (sku not in expected or sku in records or result.get("status") != "VERIFIED_EXACT_IDENTITY"
                    or not isinstance(selection, dict) or selection.get("exact_sku") != sku
                    or not isinstance(visible, dict) or not visible.get("continue_visible")
                    or str(visible.get("continue_sku") or "").upper() != sku.upper()
                    or final_url.scheme != "https" or final_url.hostname != "www.samsung.com"
                    or "/us/" not in final_url.path
                    or not final_url.path.lower().rstrip("/").endswith(f"-sku-{sku.lower()}")
                    or not isinstance(result.get("selected_configuration_raw"), dict)
                    or not isinstance(result.get("observed_ecom_group_ids"), list)
                    or len(set(result["observed_ecom_group_ids"])) != 1):
                raise ValueError("Tablet PDP identity/provenance is missing or invalid")
            snapshot_raw = (result_path.parent / "snapshot.json").read_bytes()
            specs_raw = (result_path.parent / "specs.json").read_bytes()
            if (hashlib.sha256(snapshot_raw).hexdigest() != result.get("snapshot_sha256")
                    or hashlib.sha256(specs_raw).hexdigest() != result.get("specs_sha256")):
                raise ValueError("Tablet PDP evidence hash mismatch")
            snapshot, specs = json.loads(snapshot_raw), json.loads(specs_raw)
            if snapshot.get("target_sku") != sku:
                raise ValueError("Tablet PDP snapshot target mismatch")
            computed = pdp_facts(specs, sku, family="tablet")
            if computed != result.get("pdp_facts_raw"):
                raise ValueError("Tablet Specs projection differs from saved product facts")
            claim = result.get("energy_star_claim_sources_raw")
            if not isinstance(claim, dict) or claim.get("exact_sku") != sku:
                raise ValueError("Tablet ENERGY STAR publication evidence lacks exact-SKU provenance")
            claim = {**claim, "pdp_logo_inspection_raw": snapshot.get("primary_logo_inspection"),
                "pdp_spec_surface_inspection_raw": snapshot.get("spec_surface_inspection"),
                "pdp_visible_spec_energy_star_rows_raw": snapshot.get("visible_spec_energy_star_rows", [])}
            records[sku], claims[sku], facts[sku] = result, claim, computed
    if set(products) != expected or set(records) != expected:
        raise ValueError("Tablet source products or PDP results do not cover the exact population")
    return sorted(expected), products, records, claims, facts, next(iter(source_ids))


def additional_patterns(value):
    if not isinstance(value, str):
        return []
    patterns = []
    for token in re.split(r"[;,]", value):
        token = token.strip()
        if (len(token) >= 4 and re.fullmatch(r"[A-Z0-9*./-]+", token, re.I)
                and re.search(r"[A-Z0-9]", token, re.I) and token not in patterns):
            patterns.append(token)
    return patterns


def literal_model_candidate(pattern, sku):
    """Link only byte-identical full model strings; do not interpret EPA stars."""
    if not isinstance(pattern, str) or not isinstance(sku, str) or pattern != sku:
        return None
    return {"model_pattern_raw": pattern, "exact_sku_raw": sku,
        "candidate_basis": "LITERAL_FULL_SKU_EQUALITY_ONLY"}


def build_candidates(skus, products, records, claims, facts, epa_rows, source_run_id, epa_summary, output):
    rows_by_sku = []
    type_counts = Counter()
    for sku in skus:
        candidates, seen = [], set()
        for epa_row in epa_rows:
            patterns = [("model_number", epa_row.get("model_number"))]
            patterns.extend(("additional_model_information", token)
                for token in additional_patterns(epa_row.get("additional_model_information")))
            for source_field, pattern in patterns:
                match = literal_model_candidate(pattern, sku)
                signature = (epa_row.get("source_row_id", epa_row.get("pd_id")), source_field, pattern)
                if match is None or signature in seen:
                    continue
                seen.add(signature)
                candidates.append({"candidate_source_field": source_field,
                    "model_pattern_candidate": match,
                    "epa_row_raw": {f"{key}_raw": value for key, value in epa_row.items()}})
                type_counts[str(epa_row.get("type") or "(blank)")] += 1
        rows_by_sku.append({"exact_sku": sku,
            "source_listing_raw": products[sku].get("source_claim_listing_raw"),
            "selected_configuration_raw": records[sku].get("selected_configuration_raw"),
            "pdp_product_facts_raw": facts[sku],
            "energy_star_claim_sources_raw": claims[sku],
            "epa_computer_model_pattern_candidates": candidates,
            "registration_and_publication_assessment": "NOT_EVALUATED"})
    report = {"contract": CONTRACT, "status": "SOURCE_CANDIDATES_READY", "source_validation": "PASS",
        "dataset_id": DATASET, "collection_run_id": str(os.getenv("COLLECTION_RUN_ID")),
        "collection_source_run_id": str(source_run_id), "epa_capture_run_id": epa_summary.get("capture_run_id"),
        "git_sha": os.getenv("GITHUB_SHA"), "captured_at": datetime.now(timezone.utc).isoformat(),
        "population_count": len(rows_by_sku), "epa_samsung_row_count": len(epa_rows),
        "candidate_link_count": sum(len(row["epa_computer_model_pattern_candidates"]) for row in rows_by_sku),
        "skus_with_pattern_candidates": sum(bool(row["epa_computer_model_pattern_candidates"]) for row in rows_by_sku),
        "candidate_epa_type_counts": dict(sorted(type_counts.items())),
        "epa_model_samples": [{key: row.get(key) for key in
            ("pd_id", "model_number", "model_name", "additional_model_information", "type",
             "operating_system_name", "markets")} for row in epa_rows],
        "matching_contract": "CASE_SENSITIVE_LITERAL_FULL_SKU_EQUALITY_ONLY; ASTERISK_STRINGS_RETAINED_RAW_BUT_NOT_INTERPRETED; NO_PREFIX, HYPHEN, DELETION, OR FUZZY NORMALIZATION",
        "classification": "NOT_EVALUATED_PENDING_TYPE_MARKET_CURRENT_STATUS_AND_VARIANT_MATCHING_CONTRACT",
        "scope": "Current exact-SKU Tablet PDP evidence and complete current Samsung EPA Computers V9.0 source rows; no legal applicability or severity assessment",
        "records": rows_by_sku}
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    target = out / "tablet-epa-source-candidates.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Tablet EPA source candidates\n\n")
            stream.write(f"Exact Tablet SKUs: **{len(rows_by_sku)}**; current Samsung EPA rows: **{len(epa_rows)}**; literal full-SKU candidate links: **{report['candidate_link_count']}**. Registration and publication assessment remain NOT_EVALUATED.\n\n")
            stream.write("| Exact SKU | EPA model pattern | Type | OS | Markets |\n|---|---|---|---|---|\n")
            for record in rows_by_sku:
                for candidate in record["epa_computer_model_pattern_candidates"]:
                    row = candidate["epa_row_raw"]
                    values = [record["exact_sku"], row.get("model_number_raw"), row.get("type_raw"),
                        row.get("operating_system_name_raw"), row.get("markets_raw")]
                    stream.write("| " + " | ".join(str(value or "").replace("|", "\\|") for value in values) + " |\n")
    print(json.dumps({"status": report["status"], "population_count": len(rows_by_sku),
        "epa_samsung_row_count": len(epa_rows), "candidate_link_count": report["candidate_link_count"],
        "skus_with_pattern_candidates": report["skus_with_pattern_candidates"],
        "candidate_epa_type_counts": report["candidate_epa_type_counts"],
        "classification": report["classification"]}, sort_keys=True), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--collection-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    skus, products, records, claims, facts, source_run_id = load_collection(args.collection_root, args.collection_run_id)
    capture_root = Path(args.out) / "epa-current-source"
    _, epa_rows, epa_summary = capture_epa(capture_root)
    build_candidates(skus, products, records, claims, facts, epa_rows, source_run_id, epa_summary,
        Path(args.out) / "candidates")


if __name__ == "__main__":
    main()

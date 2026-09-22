"""Capture EPA's current Samsung all-in-one washer/dryer source rows, without matching."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DATASET = "9jai-gs6t"
DATASET_NAME = "ENERGY STAR Certified Res-Combo-Washer-Dryer"
METADATA_URL = f"https://data.energystar.gov/api/views/{DATASET}.json"
ROWS_URL = f"https://data.energystar.gov/resource/{DATASET}.json"
BRAND_WHERE = "upper(brand_name) = 'SAMSUNG'"
REQUIRED = {
    "pd_id", "brand_name", "model_number", "additional_model_information",
    "special_type", "intended_market", "annual_energy_use_kwh_year",
    "volume_cubic_feet",
    "drum_capacity_for_the_dryer_in_a_combination_all_in_one_washer_dryer",
    "combined_energy_factor_cef_for_the_dryer_in_a_combination_all_in_one_washer_dryer",
    "estimated_annual_energy_use_kwh_yr_for_the_dryer_in_a_combination_all_in_one_washer_dryer",
    "date_qualified", "markets",
}


def fetch(url):
    request = Request(url, headers={"User-Agent": "RDA-G3-Dryer-Combo-EPA-Source/1.0", "Accept": "application/json"})
    with urlopen(request, timeout=45) as response:
        return response.read(), response.headers.get_content_type(), response.status


def capture(output, page_size=100):
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    meta_before_raw, kind, status = fetch(METADATA_URL)
    if status != 200 or "json" not in kind.lower():
        raise ValueError("EPA combination washer/dryer metadata unavailable")
    metadata = json.loads(meta_before_raw)
    if metadata.get("id") != DATASET or metadata.get("name") != DATASET_NAME:
        raise ValueError("EPA combination washer/dryer dataset identity changed")
    fields = [column.get("fieldName") for column in metadata.get("columns", [])]
    if not REQUIRED <= set(fields):
        raise ValueError("EPA combination washer/dryer dataset is missing required source fields")
    selected = [field for field in fields if isinstance(field, str) and re.fullmatch(r"[a-z][a-z0-9_]*", field)]
    select = ":id as source_row_id," + ",".join(selected)

    def query(params):
        body, content_type, http_status = fetch(ROWS_URL + "?" + urlencode(params))
        if http_status != 200 or "json" not in content_type.lower():
            raise ValueError("EPA combination washer/dryer query was not successful JSON")
        result = json.loads(body)
        if not isinstance(result, list) or any(not isinstance(item, dict) for item in result):
            raise ValueError("EPA combination washer/dryer query did not return records")
        return result

    count_rows = query({"$select": "count(*) as row_count", "$where": BRAND_WHERE})
    if len(count_rows) != 1 or not str(count_rows[0].get("row_count", "")).isdigit():
        raise ValueError("EPA combination washer/dryer Samsung count query malformed")
    expected = int(count_rows[0]["row_count"])
    if expected > 5000:
        raise ValueError("EPA combination washer/dryer Samsung cohort exceeds capture bound")
    rows = []
    urls = []
    for offset in range(0, expected, page_size):
        params = {"$where": BRAND_WHERE, "$select": select, "$order": ":id",
                  "$limit": str(page_size), "$offset": str(offset)}
        page = query(params)
        if not page:
            raise ValueError("EPA combination washer/dryer cohort ended before its count")
        rows.extend(page)
        urls.append(ROWS_URL + "?" + urlencode(params))
    if len(rows) != expected:
        raise ValueError("EPA combination washer/dryer pages do not match count")
    ids = [row.get("source_row_id") for row in rows]
    if any(not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("EPA combination washer/dryer rows have missing or duplicate source IDs")
    if any(not all(row.get(field) for field in ("pd_id", "brand_name", "model_number")) for row in rows):
        raise ValueError("EPA combination washer/dryer row is missing identity fields")
    if any(str(row.get("brand_name", "")).strip().upper() != "SAMSUNG" for row in rows):
        raise ValueError("EPA combination washer/dryer query returned a non-Samsung row")
    count_after = query({"$select": "count(*) as row_count", "$where": BRAND_WHERE})
    if int(count_after[0]["row_count"]) != expected:
        raise ValueError("EPA combination washer/dryer Samsung count changed during capture")
    meta_after_raw, kind, status = fetch(METADATA_URL)
    if status != 200 or "json" not in kind.lower():
        raise ValueError("EPA combination washer/dryer metadata refresh unavailable")
    metadata_after = json.loads(meta_after_raw)
    if (metadata_after.get("id") != DATASET or metadata_after.get("name") != DATASET_NAME
            or metadata.get("rowsUpdatedAt") != metadata_after.get("rowsUpdatedAt")
            or [(x.get("fieldName"), x.get("name")) for x in metadata.get("columns", [])]
            != [(x.get("fieldName"), x.get("name")) for x in metadata_after.get("columns", [])]):
        raise ValueError("EPA combination washer/dryer schema or source timestamp changed during capture")

    projection = {key: metadata.get(key) for key in ("id", "name", "rowsUpdatedAt", "viewLastModified", "publicationDate")}
    projection["columns"] = [{key: column.get(key) for key in ("fieldName", "name", "dataTypeName")}
                              for column in metadata.get("columns", []) if not str(column.get("fieldName", "")).startswith(":")]
    metadata_bytes = (json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    rows_bytes = (json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    (destination / "metadata.json").write_bytes(metadata_bytes)
    (destination / "samsung-current-rows.json").write_bytes(rows_bytes)
    report = {"contract": "G3_DRYER_COMBO_EPA_CURRENT_SOURCE_V1", "dataset_id": DATASET,
              "dataset_name": DATASET_NAME, "captured_at": datetime.now(timezone.utc).isoformat(),
              "capture_run_id": os.getenv("GITHUB_RUN_ID"), "git_sha": os.getenv("GITHUB_SHA"),
              "metadata_url": METADATA_URL, "row_page_urls": urls, "brand_condition": BRAND_WHERE,
              "page_size": page_size, "row_count": len(rows),
              "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
              "rows_sha256": hashlib.sha256(rows_bytes).hexdigest(),
              "completeness": "COUNT_MATCHED_PAGED_UNIQUE_SOURCE_IDS_AND_STABLE_SCHEMA",
              "snapshot_atomicity": "OFFSET_SOURCE_NOT_ATOMIC_BUT_COUNTS_AND_SCHEMA_STABLE_DURING_CAPTURE",
              "energy_scope": {"annual_energy_use_kwh_year": "WASHER_COMPONENT", "estimated_annual_energy_use_kwh_yr_for_the_dryer_in_a_combination_all_in_one_washer_dryer": "DRYER_COMPONENT"},
              "scope": "Official EPA current Samsung combination all-in-one washer/dryer rows; source capture only; no matching, comparison, or assessment",
              "model_matching": "NOT_EVALUATED", "assessment": "NOT_EVALUATED", "status": "PASS"}
    (destination / "capture-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## EPA current Samsung combination washer/dryer source capture\n\n")
            stream.write(f"Status: **PASS**; dataset `{DATASET}`; Samsung rows: **{len(rows)}**. Washer and dryer component energy columns are preserved separately; matching and assessment were not evaluated.\n")
            stream.write("\n| EPA model pattern | Washer annual kWh/yr | Dryer annual kWh/yr | Dryer capacity | Dryer CEF |\n|---|---:|---:|---:|---:|\n")
            for row in rows:
                cells = [row.get("model_number", ""), row.get("annual_energy_use_kwh_year", ""),
                         row.get("estimated_annual_energy_use_kwh_yr_for_the_dryer_in_a_combination_all_in_one_washer_dryer", ""),
                         row.get("drum_capacity_for_the_dryer_in_a_combination_all_in_one_washer_dryer", ""),
                         row.get("combined_energy_factor_cef_for_the_dryer_in_a_combination_all_in_one_washer_dryer", "")]
                stream.write("| " + " | ".join(str(value if value is not None else "").replace("|", "\\|").replace("\n", " ") for value in cells) + " |\n")
    print(json.dumps({"status": "PASS", "dataset_id": DATASET, "samsung_row_count": len(rows)}, sort_keys=True), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    capture(args.out)


if __name__ == "__main__":
    main()

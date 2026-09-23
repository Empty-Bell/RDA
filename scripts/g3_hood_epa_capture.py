"""Capture the complete current Samsung cohort from EPA's hood dataset, without matching."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import time
from urllib.parse import urlencode


DATASET = "8dv7-nngq"
METADATA_URL = f"https://data.energystar.gov/api/views/{DATASET}.json"
ROWS_URL = f"https://data.energystar.gov/resource/{DATASET}.json"
BRAND_WHERE = "upper(brand_name) = 'SAMSUNG'"
REQUIRED = {"pd_id", "brand_name", "model_number", "unit_type", "markets", "date_qualified",
            "airflow_1_cfm", "efficacy_1_cfm_w", "sound_level_sones"}

def fetch(url):
    request = Request(url, headers={"User-Agent": "RDA-G3-Hood-EPA-Source/1.0", "Accept": "application/json"})
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
    raise RuntimeError("EPA hood request retry loop exhausted")

def capture(output, page_size=100):
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    meta_before_raw, kind, status = fetch(METADATA_URL)
    if status != 200 or "json" not in kind.lower():
        raise ValueError("EPA hood metadata unavailable")
    metadata = json.loads(meta_before_raw)
    if metadata.get("id") != DATASET or metadata.get("name") != "ENERGY STAR Certified Ventilating Fans":
        raise ValueError("EPA hood dataset identity changed")
    fields = [column.get("fieldName") for column in metadata.get("columns", [])]
    if not REQUIRED <= set(fields):
        raise ValueError("EPA hood dataset is missing required source fields")
    selected = [field for field in fields if isinstance(field, str) and re.fullmatch(r"[a-z][a-z0-9_]*", field)]
    select = ":id as source_row_id," + ",".join(selected)

    def query(params):
        url = ROWS_URL + "?" + urlencode(params)
        body, content_type, http_status = fetch(url)
        if http_status != 200 or "json" not in content_type.lower():
            raise ValueError("EPA hood row query was not successful JSON")
        result = json.loads(body)
        if not isinstance(result, list) or any(not isinstance(item, dict) for item in result):
            raise ValueError("EPA hood query did not return an array of records")
        return result, url

    count_rows, count_url = query({"$select": "count(*) as row_count", "$where": BRAND_WHERE})
    if len(count_rows) != 1 or not str(count_rows[0].get("row_count", "")).isdigit():
        raise ValueError("EPA hood Samsung count query malformed")
    expected = int(count_rows[0]["row_count"])
    if expected > 5000:
        raise ValueError("EPA hood Samsung cohort exceeds capture bound")
    pages, urls = [], []
    for offset in range(0, expected, page_size):
        page, url = query({"$where": BRAND_WHERE, "$select": select, "$order": ":id",
                           "$limit": str(page_size), "$offset": str(offset)})
        if not page:
            raise ValueError("EPA hood cohort ended before its count")
        pages.append(page)
        urls.append(url)
    rows = [row for page in pages for row in page]
    if len(rows) != expected:
        raise ValueError("EPA hood row pages do not match count")
    if any(str(row.get("brand_name", "")).strip().upper() != "SAMSUNG" for row in rows):
        raise ValueError("EPA hood query returned a non-Samsung row")
    ids = [row.get("source_row_id") for row in rows]
    if any(not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("EPA hood rows have missing or duplicated source identities")
    if any(not all(row.get(field) for field in ("pd_id", "brand_name", "model_number")) for row in rows):
        raise ValueError("EPA hood row is missing identity fields")
    count_after, _ = query({"$select": "count(*) as row_count", "$where": BRAND_WHERE})
    if int(count_after[0]["row_count"]) != expected:
        raise ValueError("EPA hood source row count changed during capture")
    meta_after_raw, kind, status = fetch(METADATA_URL)
    if status != 200 or "json" not in kind.lower():
        raise ValueError("EPA hood metadata refresh unavailable")
    metadata_after = json.loads(meta_after_raw)
    if (metadata_after.get("id") != DATASET
            or metadata_after.get("name") != metadata.get("name")
            or metadata.get("rowsUpdatedAt") != metadata_after.get("rowsUpdatedAt")
            or [(x.get("fieldName"), x.get("name")) for x in metadata.get("columns", [])]
            != [(x.get("fieldName"), x.get("name")) for x in metadata_after.get("columns", [])]):
        raise ValueError("EPA hood schema or source update timestamp changed during capture")

    projection = {key: metadata.get(key) for key in ("id", "name", "rowsUpdatedAt", "viewLastModified", "publicationDate")}
    projection["columns"] = [{key: column.get(key) for key in ("fieldName", "name", "dataTypeName")}
                              for column in metadata.get("columns", []) if not str(column.get("fieldName", "")).startswith(":")]
    metadata_bytes = (json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    rows_bytes = (json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    (destination / "metadata.json").write_bytes(metadata_bytes)
    (destination / "samsung-current-rows.json").write_bytes(rows_bytes)
    report = {"contract": "G3_HOOD_EPA_CURRENT_SOURCE_V1", "dataset_id": DATASET,
              "captured_at": datetime.now(timezone.utc).isoformat(), "capture_run_id": os.getenv("GITHUB_RUN_ID"),
              "git_sha": os.getenv("GITHUB_SHA"), "metadata_url": METADATA_URL, "count_url": count_url,
              "row_page_urls": urls, "brand_condition": BRAND_WHERE, "page_size": page_size,
              "row_count": len(rows), "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
              "rows_sha256": hashlib.sha256(rows_bytes).hexdigest(),
              "completeness": "COUNT_MATCHED_PAGED_UNIQUE_SOURCE_IDS_AND_STABLE_SCHEMA",
              "snapshot_atomicity": "OFFSET_SOURCE_NOT_ATOMIC_BUT_COUNTS_AND_SCHEMA_STABLE_DURING_CAPTURE",
              "scope": "Official EPA current Samsung ventilating-fan dataset rows only; mixed unit types retained without hood classification, matching, or certification assessment",
              "model_matching": "NOT_EVALUATED", "assessment": "NOT_EVALUATED", "status": "PASS"}
    (destination / "capture-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("## Hood EPA current source capture\n\n")
            stream.write(f"Status: **PASS**; dataset `{DATASET}`; Samsung rows: **{len(rows)}**; schema timestamp: `{metadata.get('rowsUpdatedAt')}`. Matching and compliance were not evaluated.\n")
    print(json.dumps({"status": "PASS", "dataset_id": DATASET, "samsung_row_count": len(rows)}, sort_keys=True), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    capture(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


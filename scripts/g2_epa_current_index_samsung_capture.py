"""Capture a complete Samsung scope from EPA's current Model Index.

This is a source-contract collector only.  It does not decide whether any
Samsung SKU is certified and it does not evaluate publication claims.
"""

import hashlib
import json
import os
import argparse
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from epa_queries import BRAND_WHERE, complete_scan, decode_rows, query_url, row_count

DATASET = "8wj2-sec8"
PAGE_SIZE = 100
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
REQUIRED_FIELDS = {"pd_id", "brand_name", "model_number", "energy_star_model_identifier"}


def metadata_projection(body: bytes) -> dict:
    data = json.loads(body)
    fields = sorted(
        column.get("fieldName")
        for column in data.get("columns", [])
        if isinstance(column, dict) and isinstance(column.get("fieldName"), str)
    )
    if data.get("id") != DATASET or not REQUIRED_FIELDS <= set(fields):
        raise ValueError("Model Index schema identity invalid")
    return {
        "id": data["id"],
        "rows_updated_at": data.get("rowsUpdatedAt"),
        "view_last_modified": data.get("viewLastModified"),
        "fields": fields,
    }


def metadata_fingerprint(metadata: dict) -> dict:
    return {key: metadata[key] for key in ("id", "rows_updated_at", "view_last_modified", "fields")}


def page_rows(body: bytes) -> list[dict]:
    rows = json.loads(body)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("EPA page is not an array of records")
    for row in rows:
        if row.get("brand_name", "").upper() != "SAMSUNG":
            raise ValueError("EPA Samsung query returned a non-Samsung row")
    return rows


def duplicate_candidate_key_count(rows: list[dict]) -> int:
    keys = [tuple(str(row.get(field, "")) for field in sorted(REQUIRED_FIELDS)) for row in rows]
    return len(keys) - len(set(keys))


def page_query_params(offset: int) -> dict:
    if offset < 0 or offset % PAGE_SIZE:
        raise ValueError("EPA page offset invalid")
    # Socrata permits `*` only at the beginning of a select list.
    return {
        "$where": BRAND_WHERE,
        "$select": "*,:id as source_row_id",
        "$order": ":id",
        "$limit": PAGE_SIZE,
        "$offset": offset,
    }


def scan_projection(
    pages: list[list[dict]],
    count_before: int,
    count_after: int,
    metadata_before: dict,
    metadata_after: dict,
) -> dict:
    scan = complete_scan(
        pages,
        count_before,
        count_after,
        metadata_fingerprint(metadata_before),
        metadata_fingerprint(metadata_after),
        PAGE_SIZE,
    )
    rows = [row for page in pages for row in page]
    scan.update(
        {
            "brand_scope_where": BRAND_WHERE,
            "dataset_id": DATASET,
            "duplicate_candidate_key_count": duplicate_candidate_key_count(rows),
            "current_certification_state": "NOT_EVALUATED",
            "assessment": "NOT_EVALUATED",
        }
    )
    return scan


def source_record(
    name: str, filename: str, url: str, body: bytes, status: int, content_type: str
) -> dict:
    if status != 200 or "json" not in content_type.lower() or not body:
        raise ValueError("EPA source unavailable or invalid: " + name)
    return {
        "name": name,
        "file": filename,
        "url": url,
        "status": status,
        "content_type": content_type,
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "size_bytes": len(body),
    }


def decoded_rows(record: dict, body: bytes) -> list[dict]:
    return decode_rows(record["status"], record["content_type"], body)


def replay_capture(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    records = {record["name"]: record for record in manifest["sources"]}
    required = {"metadata-before", "metadata-after", "count-before", "count-after"}
    if not required <= set(records):
        raise ValueError("EPA Samsung-scope capture sources missing")
    bodies = {}
    for record in manifest["sources"]:
        body = (root / record["file"]).read_bytes()
        if hashlib.sha256(body).hexdigest() != record["body_sha256"]:
            raise ValueError("EPA Samsung-scope source hash does not replay")
        bodies[record["name"]] = body
    before = metadata_projection(bodies["metadata-before"])
    after = metadata_projection(bodies["metadata-after"])
    if before != manifest.get("metadata_before") or after != manifest.get("metadata_after"):
        raise ValueError("EPA Samsung-scope metadata does not replay")
    count_before = row_count(decoded_rows(records["count-before"], bodies["count-before"]))
    count_after = row_count(decoded_rows(records["count-after"], bodies["count-after"]))
    page_names = sorted(name for name in records if name.startswith("page-"))
    if not page_names:
        raise ValueError("EPA Samsung-scope terminal page missing")
    pages = [page_rows(bodies[name]) for name in page_names]
    projection = scan_projection(pages, count_before, count_after, before, after)
    if projection != manifest["scan"]:
        raise ValueError("EPA Samsung-scope scan does not replay")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out", type=Path, default=Path("runtime/g2-epa-current-index-samsung-capture")
    )
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    def fetch(name: str, url: str) -> bytes:
        filename = name + ".bin"
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,*/*;q=0.8"}
        )
        try:
            response = urllib.request.urlopen(request, timeout=45)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
        (out / filename).write_bytes(body)
        records.append(source_record(name, filename, url, body, status, content_type))
        return body

    try:
        metadata_url = f"https://data.energystar.gov/api/views/{DATASET}.json"
        before = metadata_projection(fetch("metadata-before", metadata_url))
        count_url = query_url(DATASET, {"$where": BRAND_WHERE, "$select": "count(*) as row_count"})
        count_before_body = fetch("count-before", count_url)
        count_before = row_count(decoded_rows(records[-1], count_before_body))
        pages: list[list[dict]] = []
        for index in range((count_before // PAGE_SIZE) + 1):
            page_url = query_url(DATASET, page_query_params(index * PAGE_SIZE))
            name = f"page-{index:04d}"
            pages.append(page_rows(fetch(name, page_url)))
            if len(pages[-1]) < PAGE_SIZE:
                break
        else:
            raise ValueError("EPA Samsung-scope terminal page missing")
        count_after_body = fetch("count-after", count_url)
        count_after = row_count(decoded_rows(records[-1], count_after_body))
        after = metadata_projection(fetch("metadata-after", metadata_url))
        manifest = {
            "contract": "G2_EPA_CURRENT_INDEX_SAMSUNG_SCOPE_CAPTURE_ONLY_V1",
            "status": "PASS",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "run_id": os.getenv("RDA_EXECUTION_ID", os.getenv("GITHUB_RUN_ID")),
            "github_run_id": os.getenv("GITHUB_RUN_ID"),
            "git_sha": os.getenv("GITHUB_SHA"),
            "sources": records,
            "metadata_before": before,
            "metadata_after": after,
            "scan": scan_projection(pages, count_before, count_after, before, after),
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        replay_capture(out)
    except Exception as error:
        (out / "manifest.json").write_text(
            json.dumps(
                {
                    "contract": "G2_EPA_CURRENT_INDEX_SAMSUNG_SCOPE_CAPTURE_ONLY_V1",
                    "status": "FAIL",
                    "error": str(error),
                    "sources": records,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise


if __name__ == "__main__":
    main()

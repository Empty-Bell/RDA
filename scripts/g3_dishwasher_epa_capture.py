"""Capture current official ENERGY STAR dishwasher rows for source review only."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DATASET = "q8py-6w3f"
CATALOG = f"https://data.energystar.gov/api/views/{DATASET}.json"
ROWS = f"https://data.energystar.gov/resource/{DATASET}.json"


def fetch(url: str) -> tuple[bytes, str, int]:
    request = Request(url, headers={"User-Agent": "RDA-G3-Dishwasher-Source/1.0", "Accept": "application/json"})
    with urlopen(request, timeout=60) as response:
        return response.read(), response.headers.get_content_type(), response.status


def capture(output: str | Path, limit: int = 5000) -> dict:
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    metadata_raw, metadata_type, metadata_status = fetch(CATALOG)
    if metadata_status != 200 or metadata_type != "application/json":
        raise ValueError("EPA dishwasher metadata response is unavailable")
    metadata = json.loads(metadata_raw)
    if metadata.get("id") != DATASET or "dishwasher" not in metadata.get("name", "").lower():
        raise ValueError("EPA dataset identity changed")
    required = {"pd_id", "brand_name", "model_number", "markets", "annual_energy_use_kwh_year", "date_certified", "capacity_maximum_number_of_place_settings", "water_use_gallons_cycle"}
    fields = {column.get("fieldName") for column in metadata.get("columns", [])}
    if not required <= fields:
        raise ValueError("EPA dishwasher schema is missing required fields")
    query = urlencode({"$limit": str(limit), "$where": "upper(brand_name) = 'SAMSUNG'", "$order": "pd_id"})
    rows_url = f"{ROWS}?{query}"
    rows_raw, rows_type, rows_status = fetch(rows_url)
    if rows_status != 200 or rows_type != "application/json":
        raise ValueError("EPA dishwasher current rows response is unavailable")
    rows = json.loads(rows_raw)
    if not isinstance(rows, list):
        raise ValueError("EPA dishwasher current rows response is not a list")
    metadata_path = destination / "metadata.json"
    rows_path = destination / "samsung-current-rows.json"
    metadata_path.write_bytes(metadata_raw)
    rows_path.write_bytes(rows_raw)
    report = {"contract": "G3_DISHWASHER_EPA_CURRENT_SOURCE_V1", "dataset_id": DATASET,
              "captured_at": datetime.now(timezone.utc).isoformat(), "capture_run_id": os.getenv("GITHUB_RUN_ID"),
              "git_sha": os.getenv("GITHUB_SHA"), "metadata_url": CATALOG, "rows_url": rows_url,
              "metadata_sha256": hashlib.sha256(metadata_raw).hexdigest(), "rows_sha256": hashlib.sha256(rows_raw).hexdigest(),
              "row_count": len(rows), "brand_filter": "upper(brand_name) = 'SAMSUNG'",
              "scope": "Official EPA current dishwasher source capture only; no exact-SKU matching or certification assessment",
              "model_matching": "NOT_EVALUATED", "assessment": "NOT_EVALUATED", "status": "PASS"}
    (destination / "capture-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "row_count": len(rows), "rows_sha256": report["rows_sha256"]}, sort_keys=True), flush=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=5000)
    args = parser.parse_args()
    capture(args.out, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

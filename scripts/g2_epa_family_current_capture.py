"""Capture complete Samsung refrigerator/freezer ENERGY STAR family listings."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DATASETS = ("p5st-her9", "8t9c-g3tn")
REQUIRED = {"pd_id", "brand_name", "model_number", "markets",
            "annual_energy_use_kwh_yr", "capacity_total_volume_ft3"}


def fetch(url):
    last = None
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "RDA-EPA-Family/1.0",
                                               "Accept": "application/json"}), timeout=60) as response:
                if response.status != 200 or "json" not in response.headers.get_content_type():
                    raise ValueError(f"Unexpected EPA response for {url}")
                return response.read()
        except Exception as error:
            last = error
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise ValueError(f"EPA family source unavailable: {url}") from last


def capture(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    sources = []
    for dataset in DATASETS:
        metadata_url = f"https://data.energystar.gov/api/views/{dataset}.json"
        row_url = f"https://data.energystar.gov/resource/{dataset}.json?" + urlencode({
            "$where": "upper(brand_name) = 'SAMSUNG'", "$order": "pd_id", "$limit": "5000"})
        before, body, after = fetch(metadata_url), fetch(row_url), fetch(metadata_url)
        metadata = json.loads(before)
        fields = {column.get("fieldName") for column in metadata.get("columns", [])}
        after_metadata = json.loads(after)
        after_fields = {column.get("fieldName") for column in after_metadata.get("columns", [])}
        if (metadata.get("id") != dataset or not REQUIRED <= fields
                or not ({"date_certified", "date_qualified"} & fields)
                or (metadata.get("id"), metadata.get("rowsUpdatedAt"), fields)
                != (after_metadata.get("id"), after_metadata.get("rowsUpdatedAt"), after_fields)):
            raise ValueError(f"EPA {dataset} metadata identity/schema changed")
        rows = json.loads(body)
        if (not isinstance(rows, list) or len(rows) >= 5000 or not rows
                or any(str(row.get("brand_name") or "").upper() != "SAMSUNG"
                       or not str(row.get("pd_id") or "").isdigit() for row in rows)):
            raise ValueError(f"EPA {dataset} Samsung result is incomplete or invalid")
        (out / f"{dataset}-metadata.json").write_bytes(before)
        (out / f"{dataset}-rows.json").write_bytes(body)
        sources.append({"dataset_id": dataset, "metadata_url": metadata_url, "rows_url": row_url,
                        "metadata_sha256": hashlib.sha256(before).hexdigest(),
                        "rows_sha256": hashlib.sha256(body).hexdigest(), "row_count": len(rows)})
    result = {"contract": "RDA_EPA_REFRIGERATION_FAMILY_CURRENT_V1", "status": "PASS",
              "capture_run_id": os.getenv("GITHUB_RUN_ID"), "captured_at": datetime.now(timezone.utc).isoformat(),
              "sources": sources}
    (out / "capture-summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    print(json.dumps(capture(args.out), sort_keys=True), flush=True)

"""Capture EPA Computers V9.0 Samsung rows and build raw exact-SKU candidates."""
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
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from epa_only_rules import model_pattern_candidate
from source_contract import computer_selection, epa_contract, pdp_facts

DATASET = "rxdj-2c88"
BASE = f"https://data.energystar.gov/resource/{DATASET}.json"
META_URL = f"https://data.energystar.gov/api/views/{DATASET}.json"
BRAND_WHERE = "upper(brand_name) = 'SAMSUNG'"
CONTRACT = "G3_COMPUTER_EPA_SOURCE_CANDIDATES_V1"
COLLECTION_CONTRACT = "G3_COMPUTER_EXACT_SKU_PDP_V1"
FIELDS = ("pd_id", "brand_name", "model_name", "model_number", "additional_model_information", "upc",
          "type", "operating_system_name", "system_memory_ram_gb", "total_battery_capacity_watt_hours",
          "external_power_supply_rated_power_w", "off_mode_watts", "sleep_mode_watts", "long_idle_watts",
          "short_idle_watts", "tec_of_model_kwh", "date_certified", "markets", "energy_star_model_identifier")


def fetch(url):
    request = Request(url, headers={"User-Agent": "RDA-G3-Computer-EPA-Source/1.0", "Accept": "application/json"})
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


def query(params):
    body, kind, status = fetch(BASE + "?" + urlencode(params))
    if status != 200 or "json" not in kind.lower():
        raise ValueError("EPA Computers query was not successful JSON")
    rows = json.loads(body)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("EPA Computers query response is not an array of records")
    return rows


def capture_epa(output, page_size=100):
    out = Path(output); out.mkdir(parents=True, exist_ok=True)
    raw_meta, kind, status = fetch(META_URL)
    if status != 200 or "json" not in kind.lower():
        raise ValueError("EPA Computers metadata unavailable")
    metadata = json.loads(raw_meta)
    if metadata.get("id") != DATASET or metadata.get("name") != "ENERGY STAR Certified Computers V9.0":
        raise ValueError("EPA Computers dataset identity changed")
    count = query({"$select": "count(*) as row_count", "$where": BRAND_WHERE})
    if len(count) != 1 or not str(count[0].get("row_count", "")).isdigit():
        raise ValueError("EPA Samsung computer count response malformed")
    expected = int(count[0]["row_count"])
    if expected < 1 or expected > 10000:
        raise ValueError("EPA Samsung computer cohort is outside the bounded capture range")
    available = {column.get("fieldName") for column in metadata.get("columns", [])}
    if not set(FIELDS) <= available:
        raise ValueError("EPA Computers metadata is missing required identity/configuration columns")
    all_fields = [column.get("fieldName") for column in metadata.get("columns", [])
                  if isinstance(column.get("fieldName"), str) and re.fullmatch(r"[a-z][a-z0-9_]*", column["fieldName"])]
    select = ":id as source_row_id," + ",".join(all_fields)
    rows = []
    urls = []
    for offset in range(0, expected, page_size):
        params = {"$where": BRAND_WHERE, "$select": select, "$order": ":id",
                  "$limit": str(page_size), "$offset": str(offset)}
        url = BASE + "?" + urlencode(params)
        page = query(params)
        if not page:
            raise ValueError("EPA Samsung computer cohort ended before count")
        rows.extend(page); urls.append(url)
    if len(rows) != expected or any(str(row.get("brand_name", "")).strip().upper() != "SAMSUNG" for row in rows):
        raise ValueError("EPA Samsung computer pages do not match the complete Samsung count")
    ids = [row.get("source_row_id") for row in rows]
    if any(not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("EPA Samsung computer rows have missing or duplicate IDs")
    epa_contract(metadata, rows, dataset=DATASET)
    count_after = query({"$select": "count(*) as row_count", "$where": BRAND_WHERE})
    raw_meta_after, kind_after, status_after = fetch(META_URL)
    metadata_after = json.loads(raw_meta_after) if status_after == 200 and "json" in kind_after.lower() else {}
    if (int(count_after[0]["row_count"]) != expected or metadata_after.get("id") != DATASET
            or metadata_after.get("rowsUpdatedAt") != metadata.get("rowsUpdatedAt")):
        raise ValueError("EPA Computers source count/schema timestamp changed during capture")
    projection = {key: metadata.get(key) for key in ("id", "name", "rowsUpdatedAt", "viewLastModified", "publicationDate")}
    projection["columns"] = [{key: col.get(key) for key in ("fieldName", "name", "dataTypeName")}
                              for col in metadata.get("columns", []) if not str(col.get("fieldName", "")).startswith(":")]
    meta_bytes = (json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    rows_bytes = (json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    (out / "metadata.json").write_bytes(meta_bytes); (out / "samsung-current-rows.json").write_bytes(rows_bytes)
    summary = {"contract": "G3_COMPUTER_EPA_CURRENT_SOURCE_V1", "dataset_id": DATASET,
        "capture_run_id": os.getenv("GITHUB_RUN_ID"), "captured_at": datetime.now(timezone.utc).isoformat(),
        "rows_updated_at": metadata.get("rowsUpdatedAt"), "row_count": len(rows), "brand_condition": BRAND_WHERE,
        "page_size": page_size, "row_page_urls": urls,
        "metadata_sha256": hashlib.sha256(meta_bytes).hexdigest(),
        "rows_sha256": hashlib.sha256(rows_bytes).hexdigest(), "status": "PASS",
        "completeness": "COUNT_MATCHED_PAGED_UNIQUE_SOURCE_IDS_STABLE_ROW_COUNT_AND_UPDATE_TIMESTAMP",
        "matching_and_assessment": "NOT_EVALUATED"}
    (out / "capture-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rows, summary


def load_collection(root, expected_run_id):
    root = Path(root)
    dirs = sorted(path for path in root.glob("shard-*") if path.is_dir())
    summaries = [json.loads((path / "shard-summary.json").read_bytes()) for path in dirs]
    if len(summaries) != 3 or any(row.get("contract") != COLLECTION_CONTRACT or row.get("status") != "PASS"
            or str(row.get("collection_run_id")) != str(expected_run_id) for row in summaries):
        raise ValueError("Computer collection shards are incomplete or from the wrong run")
    expected = set(summaries[0].get("all_population_skus", []))
    assigned = [sku for row in summaries for sku in row.get("assigned_skus", [])]
    if len(expected) != 24 or len(assigned) != 24 or set(assigned) != expected or len(set(assigned)) != 24:
        raise ValueError("Computer collection shards do not cover the 24 exact SKUs once")
    if len({row.get("source_run_id") for row in summaries}) != 1 or any(
            set(row.get("all_population_skus", [])) != expected for row in summaries):
        raise ValueError("Computer collection source-run/population identity changed across shards")
    products, claims, facts = {}, {}, {}
    for shard in dirs:
        for path in sorted((shard / "pdp").glob("*/result.json")):
            result = json.loads(path.read_bytes()); sku = result.get("exact_sku")
            if sku not in expected or sku in products or result.get("status") != "VERIFIED_EXACT_IDENTITY":
                raise ValueError("Computer PDP result is missing, duplicated, failed, or outside population")
            config = result.get("selected_configuration_raw")
            if not isinstance(config, dict) or computer_selection(config, sku).get("exact_sku") != sku:
                raise ValueError("Computer selected configuration provenance is missing or invalid")
            snapshot_raw = (path.parent / "snapshot.json").read_bytes()
            specs_raw = (path.parent / "specs.json").read_bytes()
            if (hashlib.sha256(snapshot_raw).hexdigest() != result.get("snapshot_sha256")
                    or hashlib.sha256(specs_raw).hexdigest() != result.get("specs_sha256")):
                raise ValueError("Computer PDP evidence hash mismatch")
            snapshot, specs = json.loads(snapshot_raw), json.loads(specs_raw)
            if snapshot.get("target_sku") != sku:
                raise ValueError("Computer PDP snapshot target mismatch")
            computed = pdp_facts(specs, sku, family="computer")
            if computed != result.get("pdp_facts_raw"):
                raise ValueError("Computer PDP Specs projection differs from saved facts")
            claim = result.get("energy_star_claim_sources_raw")
            if not isinstance(claim, dict) or claim.get("exact_sku") != sku:
                raise ValueError("Computer ENERGY STAR publication claim lacks exact-SKU provenance")
            products[sku] = result; claims[sku] = claim; facts[sku] = computed
    if set(products) != expected:
        raise ValueError("Computer PDP results do not match the full 24-SKU source population")
    return sorted(expected), products, claims, facts, str(summaries[0]["source_run_id"])


def additional_patterns(value):
    if not isinstance(value, str):
        return []
    out = []
    for token in re.split(r"[;,]", value):
        token = token.strip()
        if len(token) >= 4 and re.fullmatch(r"[A-Z0-9*./-]+", token, re.I) and re.search(r"[A-Z0-9]", token, re.I) and token not in out:
            out.append(token)
    return out


def build_candidates(skus, products, claims, facts, epa_rows, source_run_id, epa_summary, output):
    records = []
    type_counts = Counter()
    for sku in skus:
        candidates = []
        for row in epa_rows:
            patterns = [("model_number", row.get("model_number"))]
            patterns.extend(("additional_model_information", token)
                            for token in additional_patterns(row.get("additional_model_information")))
            seen = set()
            for source_field, pattern in patterns:
                match = model_pattern_candidate(pattern, sku)
                signature = (source_field, pattern)
                if match is None or signature in seen:
                    continue
                seen.add(signature)
                candidates.append({"candidate_source_field": source_field, "model_pattern_candidate": match,
                    "epa_row_raw": {f"{key}_raw": value for key, value in row.items()}})
                type_counts[str(row.get("type") or "(blank)")] += 1
        records.append({"exact_sku": sku, "source_leg": products[sku].get("source_leg"),
            "selected_configuration_raw": products[sku].get("selected_configuration_raw"),
            "pdp_product_facts_raw": facts[sku], "energy_star_claim_sources_raw": claims[sku],
            "epa_computer_model_pattern_candidates": candidates,
            "registration_and_publication_assessment": "NOT_EVALUATED"})
    report = {"contract": CONTRACT, "status": "SOURCE_CANDIDATES_READY", "source_validation": "PASS",
        "dataset_id": DATASET, "collection_run_id": str(os.getenv("COLLECTION_RUN_ID")),
        "collection_source_run_id": source_run_id, "epa_capture_run_id": epa_summary.get("capture_run_id"),
        "git_sha": os.getenv("GITHUB_SHA"), "captured_at": datetime.now(timezone.utc).isoformat(),
        "population_count": len(records), "epa_samsung_row_count": len(epa_rows),
        "candidate_link_count": sum(len(row["epa_computer_model_pattern_candidates"]) for row in records),
        "skus_with_pattern_candidates": sum(bool(row["epa_computer_model_pattern_candidates"]) for row in records),
        "candidate_epa_type_counts": dict(sorted(type_counts.items())),
        "matching_contract": "Literal SKU equality or positional EPA model-number/additional-model token candidate; each * consumes one alphanumeric character; no leading-L omission or other normalization; candidate is source evidence, not a confirmed certification match.",
        "classification": "NOT_EVALUATED pending review of candidate type, OS, market, and model-pattern examples",
        "scope": "Current Samsung Computer PDP evidence and complete current Samsung EPA Computers V9.0 source rows; no legal applicability or severity assessment",
        "records": records}
    out = Path(output); out.mkdir(parents=True, exist_ok=True)
    (out / "computer-epa-source-candidates.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Computer EPA model-pattern candidates\n\n")
            stream.write(f"Exact PDP SKUs: **{len(records)}**; current Samsung EPA rows: **{len(epa_rows)}**; candidate links: **{report['candidate_link_count']}**. No compliance decision was applied.\n\n")
            stream.write("| Exact SKU | EPA pattern | Type | OS | Markets | PDP option evidence |\n|---|---|---|---|---|---|\n")
            for record in records:
                options = record["selected_configuration_raw"].get("selected_controls", [])
                label = ", ".join(str(x.get("label")) for x in options if x.get("label"))
                for candidate in record["epa_computer_model_pattern_candidates"]:
                    row = candidate["epa_row_raw"]
                    values = [record["exact_sku"], row.get("model_number_raw"), row.get("type_raw"),
                              row.get("operating_system_name_raw"), row.get("markets_raw"), label]
                    stream.write("| " + " | ".join(str(value or "").replace("|", "\\|") for value in values) + " |\n")
            stream.write("\nType, OS, market, and configuration are shown as evidence. Candidate links are not treated as confirmed registrations.\n")
    print(json.dumps({"status": report["status"], "population_count": len(records),
        "epa_samsung_row_count": len(epa_rows), "candidate_link_count": report["candidate_link_count"],
        "skus_with_pattern_candidates": report["skus_with_pattern_candidates"],
        "candidate_epa_type_counts": report["candidate_epa_type_counts"],
        "examples": [{"sku": row["exact_sku"], "candidates":[{
            "pattern": c["epa_row_raw"].get("model_number_raw"), "type": c["epa_row_raw"].get("type_raw"),
            "os": c["epa_row_raw"].get("operating_system_name_raw"), "markets": c["epa_row_raw"].get("markets_raw")}
            for c in row["epa_computer_model_pattern_candidates"][:3]]} for row in records if row["epa_computer_model_pattern_candidates"]][:12]}, sort_keys=True), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-root", required=True); parser.add_argument("--collection-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    skus, products, claims, facts, source_run = load_collection(args.collection_root, args.collection_run_id)
    rows, summary = capture_epa(Path(args.out) / "epa")
    build_candidates(skus, products, claims, facts, rows, source_run, summary, Path(args.out) / "candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

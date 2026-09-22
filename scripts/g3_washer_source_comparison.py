"""Build same-run Washer PDP/label/EPA candidate comparisons without assessment."""

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re


CONTRACT = "G3_WASHER_SOURCE_COMPARISON_CANDIDATES_V1"
MODEL_PATTERN_CHARS = re.compile(r"[A-Z0-9*/?./-]+\Z", re.I)
ENERGY_TOKEN = re.compile(r"(?<![\w.])(?P<value>\d+(?:[.,]\d+)?)\s*kwh\b", re.I)
US_MARKET = re.compile(r"\b(?:US|USA|UNITED STATES(?: OF AMERICA)?)\b", re.I)


def read_json(path):
    return json.loads(Path(path).read_bytes())


def model_prefix_match(pattern, exact_sku):
    if not isinstance(pattern, str) or not MODEL_PATTERN_CHARS.fullmatch(pattern) or not isinstance(exact_sku, str):
        return None
    expression = "^" + "".join("[A-Z0-9]" if char == "*" else re.escape(char.upper()) for char in pattern)
    match = re.match(expression, exact_sku.upper())
    if not match:
        return None
    return {"pattern_raw": pattern, "exact_sku_raw": exact_sku,
            "match_kind": "POSITIONAL_PREFIX; * = ONE A-Z/0-9 CHARACTER",
            "matched_prefix_raw": exact_sku[:len(pattern)],
            "unmatched_sku_suffix_raw": exact_sku[len(pattern):]}


def normalized_pattern_match(pattern, exact_sku):
    """Diagnostic only: retry positional wildcard matching after removing separators."""
    if not isinstance(pattern, str) or not isinstance(exact_sku, str):
        return None
    compact_pattern = re.sub(r"[^A-Z0-9*]", "", pattern.upper())
    compact_sku = re.sub(r"[^A-Z0-9]", "", exact_sku.upper())
    if not compact_pattern or not re.fullmatch(r"[A-Z0-9*]+", compact_pattern):
        return None
    expression = "^" + "".join("[A-Z0-9]" if char == "*" else re.escape(char) for char in compact_pattern)
    if not re.match(expression, compact_sku):
        return None
    return {"epa_model_pattern_raw": pattern, "normalized_sku_raw": compact_sku,
            "normalized_epa_pattern": compact_pattern,
            "normalization": "PUNCTUATION_REMOVED_FOR_DIAGNOSTIC_ONLY; * = ONE A-Z/0-9 CHARACTER"}


def near_epa_patterns(exact_sku, epa_rows, limit=3):
    sku_compact = re.sub(r"[^A-Z0-9]", "", exact_sku.upper())
    candidates = []
    for row in epa_rows:
        raw = row.get("model_number")
        if not isinstance(raw, str):
            continue
        literal = re.sub(r"[^A-Z0-9]", "", raw.upper().replace("*", ""))
        common = 0
        for left, right in zip(sku_compact, literal):
            if left != right:
                break
            common += 1
        if common >= 5:
            candidates.append({"model_number_raw": raw, "common_leading_characters_after_punctuation_removal": common,
                               "annual_energy_raw": row.get("annual_energy_use_kwh_year"),
                               "markets_raw": row.get("markets"), "pd_id": row.get("pd_id")})
    return sorted(candidates, key=lambda row: (-row["common_leading_characters_after_punctuation_removal"],
                                                row["model_number_raw"]))[:limit]


def decimal_value(raw):
    if not isinstance(raw, str):
        return None
    token = raw.replace(",", ".")
    if not re.fullmatch(r"\d+(?:\.\d+)?", token):
        return None
    try:
        value = Decimal(token)
    except InvalidOperation:
        return None
    return format(value.normalize(), "f")


def extract_kwh(raw):
    if not isinstance(raw, str):
        return None
    match = ENERGY_TOKEN.search(raw)
    return decimal_value(match.group("value")) if match else None


def us_market_scope(raw):
    if isinstance(raw, list):
        values = [str(value) for value in raw]
        return "US_MARKET_LISTED" if any(US_MARKET.search(value) for value in values) else "US_MARKET_NOT_LISTED"
    if isinstance(raw, str) and raw.strip():
        return "US_MARKET_LISTED" if US_MARKET.search(raw) else "US_MARKET_NOT_LISTED"
    return "MARKET_SCOPE_UNKNOWN"


def collection_inputs(collection_root, expected_run_id):
    root = Path(collection_root)
    summary = read_json(root / "collection-summary.json")
    if summary.get("status") != "PASS" or str(summary.get("collection_run_id")) != str(expected_run_id):
        raise ValueError("PDP collection artifact is not the requested successful same-run source")
    products = read_json(root / "products.json")
    results = [read_json(path) for path in sorted(root.glob("pdp/*/result.json"))]
    if (not isinstance(products, list) or len(results) != summary.get("coverage", {}).get("population_count")
            or len({x.get("exact_sku") for x in results}) != len(results)):
        raise ValueError("Washer PDP collection population is incomplete or duplicated")
    if any(result.get("status") != "VERIFIED_EXACT_IDENTITY" for result in results):
        raise ValueError("Washer PDP collection contains an unverified exact SKU")
    product_by_sku = {row.get("exact_sku"): row for row in products}
    if set(product_by_sku) != {row.get("exact_sku") for row in results}:
        raise ValueError("Washer PDP listing and result SKU populations differ")
    return {row["exact_sku"]: row for row in results}, product_by_sku, summary


def epa_inputs(epa_root, expected_run_id):
    root = Path(epa_root)
    summary = read_json(root / "capture-summary.json")
    raw = (root / "samsung-current-rows.json").read_bytes()
    if (summary.get("status") != "PASS" or summary.get("dataset_id") != "bghd-e2wd"
            or str(summary.get("capture_run_id")) != str(expected_run_id)
            or hashlib.sha256(raw).hexdigest() != summary.get("rows_sha256")):
        raise ValueError("EPA source rows are not the requested same-run verified capture")
    rows = json.loads(raw)
    if not isinstance(rows, list) or len(rows) != summary.get("row_count"):
        raise ValueError("EPA Samsung source row count does not match capture summary")
    return rows, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", required=True)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--collection-run-id", required=True)
    parser.add_argument("--epa-root", required=True)
    parser.add_argument("--epa-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    review = read_json(Path(args.review_root) / "review-queue.json")
    if (review.get("status") != "PASS" or review.get("contract") != "G3_WASHER_ENERGYGUIDE_RAW_CANDIDATE_REVIEW_V1"
            or str(review.get("retrieval_run_id")) != str(args.epa_run_id)):
        raise ValueError("Washer raw-label review is not bound to the same EPA/PDF retrieval run")
    pdp_by_sku, product_by_sku, pdp_summary = collection_inputs(args.collection_root, args.collection_run_id)
    if str(review.get("collection_run_id")) != str(args.collection_run_id):
        raise ValueError("Washer review table is not bound to the same PDP collection run")
    epa_rows, epa_summary = epa_inputs(args.epa_root, args.epa_run_id)
    population = sorted(pdp_by_sku)
    if review.get("sku_population_count") != len(population):
        raise ValueError("Washer PDP and label-review SKU populations differ")

    label_by_sku = {sku: [] for sku in population}
    for entry in review.get("entries", []):
        models = entry.get("model_candidates_raw", [])
        energies = [row for row in entry.get("annual_energy_candidates_raw", [])
                    if row.get("role") == "ANNUAL_CAPTION_CONTEXT"]
        for sku in entry.get("exact_skus", []):
            if sku not in label_by_sku:
                raise ValueError("Washer label review contains SKU outside the PDP population")
            label_by_sku[sku].append({"pdf_sha256": entry.get("pdf_sha256"),
                                      "model_candidates_raw": models,
                                      "annual_energy_candidates_raw": energies,
                                      "capacity_candidates_raw": entry.get("capacity_candidates_raw", []),
                                      "review_flags": entry.get("review_flags", [])})
    if any(not label_by_sku[sku] for sku in population if sku not in review.get("skus_without_support_document", [])):
        raise ValueError("A SKU with a Support-declared document is missing its label review record")

    table = []
    for sku in population:
        pdp = pdp_by_sku[sku]
        pdp_facts = pdp.get("pdp_facts_raw", {})
        product = product_by_sku[sku]
        listing = product.get("source_claim_listing_raw", {})
        label_records = label_by_sku[sku]
        label_matches = []
        label_energies = []
        label_patterns = []
        for document in label_records:
            for model in document["model_candidates_raw"]:
                pattern = model.get("value_raw")
                if pattern and pattern not in label_patterns:
                    label_patterns.append(pattern)
                match = model_prefix_match(pattern, sku)
                if match:
                    label_matches.append({**match, "pdf_sha256": document["pdf_sha256"],
                                          "context_raw": model.get("context_raw"),
                                          "evidence_layer": model.get("evidence_layer")})
            for energy in document["annual_energy_candidates_raw"]:
                label_energies.append({"value_raw": energy.get("value_raw"),
                                       "kwh_decimal_candidate": decimal_value(energy.get("value_raw")),
                                       "role": energy.get("role"),
                                       "evidence_layer": energy.get("evidence_layer"),
                                       "context_raw": energy.get("context_raw"),
                                       "pdf_sha256": document["pdf_sha256"]})

        pdp_energies = []
        for field in pdp_facts.get("energy_consumption_raw", []):
            raw_value = field.get("value")
            pdp_energies.append({"value_raw": raw_value, "kwh_decimal_candidate": extract_kwh(raw_value),
                                 "field_name_raw": field.get("name"), "field_group_raw": field.get("group")})

        epa_matches = []
        epa_normalized_matches = []
        for row in epa_rows:
            model_raw = row.get("model_number")
            match = model_prefix_match(model_raw, sku)
            if match:
                epa_matches.append({**match, "pd_id": row.get("pd_id"), "model_number_raw": model_raw,
                                    "annual_energy_raw": row.get("annual_energy_use_kwh_year"),
                                    "annual_energy_kwh_decimal_candidate": decimal_value(row.get("annual_energy_use_kwh_year")),
                                    "markets_raw": row.get("markets"), "market_scope_candidate": us_market_scope(row.get("markets")),
                                    "date_qualified_raw": row.get("date_qualified"),
                                    "load_configuration_raw": row.get("load_configuration"),
                                    "special_type_raw": row.get("special_type"),
                                    "combo_dryer_energy_raw": row.get("estimated_annual_energy_use_kwh_yr_for_the_dryer_in_a_combination_all_in_one_washer_dryer"),
                                    "additional_model_information_raw": row.get("additional_model_information")})
            normalized_match = normalized_pattern_match(model_raw, sku)
            if normalized_match:
                epa_normalized_matches.append({**normalized_match, "pd_id": row.get("pd_id"),
                                               "annual_energy_raw": row.get("annual_energy_use_kwh_year"),
                                               "markets_raw": row.get("markets"),
                                               "strict_match_already_found": bool(match)})

        values = {
            "PDP": sorted({x["kwh_decimal_candidate"] for x in pdp_energies if x["kwh_decimal_candidate"] is not None}),
            "LABEL": sorted({x["kwh_decimal_candidate"] for x in label_energies if x["kwh_decimal_candidate"] is not None}),
            "EPA_US_MARKET_CANDIDATE": sorted({x["annual_energy_kwh_decimal_candidate"] for x in epa_matches
                           if x["market_scope_candidate"] == "US_MARKET_LISTED"
                           if x["annual_energy_kwh_decimal_candidate"] is not None}),
        }
        source_counts = {key: len(value) for key, value in values.items()}
        if any(count == 0 for count in source_counts.values()):
            energy_comparison = "MISSING_SOURCE_VALUE_OR_MODEL_ROW"
        elif len({number for group in values.values() for number in group}) == 1 and all(count == 1 for count in source_counts.values()):
            energy_comparison = "ALL_THREE_SOURCES_HAVE_SAME_EXACT_VALUE"
        elif len({number for group in values.values() for number in group}) == 1:
            energy_comparison = "AVAILABLE_VALUES_EQUAL_BUT_SOURCE_HAS_MULTIPLE_CANDIDATES"
        else:
            energy_comparison = "SOURCE_VALUES_DIFFER"
        table.append({"exact_sku": sku, "pdp_title_raw": listing.get("modelName"),
                      "pdp_identity_contract": pdp.get("identity_contract"),
                      "pdp_source_provenance": {"final_url_raw": pdp.get("final_url"),
                                                "snapshot_sha256": pdp.get("snapshot_sha256"),
                                                "bridge_sha256": (pdp.get("bridge") or {}).get("sha256")},
                      "pdp_energy_candidates_raw": pdp_energies,
                      "label_document_count": len(label_records), "label_model_patterns_raw": label_patterns,
                      "label_prefix_matches": label_matches, "label_annual_energy_candidates_raw": label_energies,
                      "epa_current_model_matches": epa_matches,
                      "epa_match_count": len(epa_matches), "source_kwh_values": values,
                      "epa_normalized_pattern_matches_diagnostic_only": epa_normalized_matches,
                      "epa_near_pattern_candidates_diagnostic_only": near_epa_patterns(sku, epa_rows) if not epa_matches else [],
                      "energy_comparison_candidate": energy_comparison,
                      "model_comparison": {"pdp": "EXACT_SKU_IDENTITY_VERIFIED",
                                           "label": "ONE_OR_MORE_PREFIX_PATTERNS_MATCH" if label_matches else "NO_LABEL_PATTERN_MATCH",
                                           "epa_current": "ONE_OR_MORE_CURRENT_ROWS_MATCH" if epa_matches else "NO_CURRENT_EPA_MODEL_ROW_MATCH"},
                      "combo_routing": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"})

    report = {"contract": CONTRACT, "status": "PASS", "review_run_id": review.get("review_queue_run_id"),
              "collection_run_id": str(args.collection_run_id), "epa_capture_run_id": str(args.epa_run_id),
              "comparison_run_id": os.getenv("GITHUB_RUN_ID"), "git_sha": os.getenv("GITHUB_SHA"),
              "captured_at": datetime.now(timezone.utc).isoformat(), "population_count": len(population),
              "epa_samsung_current_row_count": len(epa_rows),
              "model_pattern_contract": "Raw exact SKU is unchanged; each * consumes one A-Z/0-9 character from its beginning; any remaining exact-SKU suffix is retained verbatim and reported.",
              "scope": "Same-run US Washer PDP, Support-label, and EPA current candidate comparison; EPA annual-energy candidates are limited to rows whose market field explicitly lists US/USA/United States; no routing, pass/low/high, or compliance decision",
              "counts": {name: sum(row["energy_comparison_candidate"] == name for row in table)
                         for name in ("ALL_THREE_SOURCES_HAVE_SAME_EXACT_VALUE",
                                      "AVAILABLE_VALUES_EQUAL_BUT_SOURCE_HAS_MULTIPLE_CANDIDATES",
                                      "SOURCE_VALUES_DIFFER", "MISSING_SOURCE_VALUE_OR_MODEL_ROW")},
              "rows": table}
    destination = Path(args.out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "source-comparison-candidates.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("## Washer PDP / label / EPA comparison candidates\n\n")
            stream.write(f"Exact SKUs: **{len(population)}**; EPA Samsung current rows captured: **{len(epa_rows)}**. No assessment or severity was applied.\n\n")
            stream.write("| Exact SKU | PDP kWh | Label pattern(s) / kWh | EPA model row(s) / kWh | Comparison candidate |\n|---|---|---|---|---|\n")
            for row in table:
                label = "; ".join(f"{p}→{','.join(sorted({x['kwh_decimal_candidate'] for x in row['label_annual_energy_candidates_raw'] if x['pdf_sha256'] == doc['pdf_sha256'] and x['kwh_decimal_candidate']}))}" for doc in row["label_prefix_matches"] for p in [doc["pattern_raw"]])
                epa = "; ".join(f"{item['model_number_raw']}→{item['annual_energy_raw']} ({item['markets_raw']})" for item in row["epa_current_model_matches"])
                pdp_values = ", ".join(sorted({x["kwh_decimal_candidate"] for x in row["pdp_energy_candidates_raw"] if x["kwh_decimal_candidate"]}))
                cells = [row["exact_sku"], pdp_values, label or "no matched label pattern", epa or "no current EPA model row", row["energy_comparison_candidate"]]
                stream.write("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", " ") for cell in cells) + " |\n")
            unresolved_epa = [row for row in table if not row["epa_current_model_matches"]]
            if unresolved_epa:
                stream.write("\n### EPA no-row model diagnostics (not matches or findings)\n\n")
                stream.write("Punctuation-normalized candidates are diagnostic only; the exact-SKU match result above is unchanged.\n\n")
                stream.write("| Exact SKU | Normalized candidate row(s) | Closest EPA model pattern(s) / common prefix length |\n|---|---|---|\n")
                for row in unresolved_epa:
                    normalized = "; ".join(f"{item['epa_model_pattern_raw']} → {item['annual_energy_raw']} ({item['markets_raw']})" for item in row["epa_normalized_pattern_matches_diagnostic_only"]) or "none"
                    near = "; ".join(f"{item['model_number_raw']} ({item['common_leading_characters_after_punctuation_removal']} chars)" for item in row["epa_near_pattern_candidates_diagnostic_only"]) or "none"
                    stream.write(f"| {row['exact_sku']} | {normalized} | {near} |\n")
    print(json.dumps({"status": report["status"], "population_count": len(population),
                      "epa_samsung_current_row_count": len(epa_rows), "counts": report["counts"],
                      "comparison_table": table}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

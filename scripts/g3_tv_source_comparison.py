"""Build same-run TV PDP/label/EPA candidate comparisons without assessment."""

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re


CONTRACT = "G3_TV_SOURCE_COMPARISON_CANDIDATES_V1"
MODEL_PATTERN_CHARS = re.compile(r"[A-Z0-9*/?./-]+\Z", re.I)
ENERGY_TOKEN = re.compile(r"(?<![\w.])(?P<value>\d+(?:[.,]\d+)?)\s*kwh\b", re.I)
WATT_TOKEN = re.compile(r"(?<![\w.])(?P<value>\d+(?:[.,]\d+)?)\s*w\b", re.I)
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
                               "annual_energy_raw": row.get("reported_annual_energy_consumption_kwh"),
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


def extract_watts(raw):
    if not isinstance(raw, str):
        return None
    match = WATT_TOKEN.search(raw)
    return decimal_value(match.group("value")) if match else None


def epa_watts(raw):
    if raw is None:
        return None
    return extract_watts(str(raw)) or decimal_value(str(raw))


def compare_single_candidates(left, right, left_missing, right_missing):
    left = sorted(set(value for value in left if value is not None))
    right = sorted(set(value for value in right if value is not None))
    if not left:
        return {"status": left_missing, "left_candidates": left, "right_candidates": right}
    if not right:
        return {"status": right_missing, "left_candidates": left, "right_candidates": right}
    if len(left) != 1 or len(right) != 1:
        return {"status": "MULTIPLE_VALUE_CANDIDATES", "left_candidates": left, "right_candidates": right}
    return {"status": "EXACT_VALUE_MATCH" if left[0] == right[0] else "VALUES_DIFFER",
            "left_candidates": left, "right_candidates": right}


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
    if summary.get("status") not in ("PASS", "FAILED") or str(summary.get("collection_run_id")) != str(expected_run_id):
        raise ValueError("PDP collection artifact is not the requested complete same-run source")
    products = read_json(root / "products.json")
    results = [read_json(path) for path in sorted(root.glob("pdp/*/result.json"))]
    if not isinstance(products, list) or len(products) != summary.get("coverage", {}).get("population_count"):
        raise ValueError("TV PDP collection population is incomplete or duplicated")
    result_by_sku = {x.get("exact_sku"): x for x in results}
    product_by_sku = {row.get("exact_sku"): row for row in products}
    coverage_rows = summary.get("coverage", {}).get("rows", [])
    coverage_by_sku = {row.get("exact_sku"): row for row in coverage_rows}
    if (len(product_by_sku) != len(products) or len(result_by_sku) != len(results)
            or len(coverage_by_sku) != len(coverage_rows)
            or not set(result_by_sku) <= set(product_by_sku)
            or set(product_by_sku) != set(coverage_by_sku)):
        raise ValueError("TV PDP listing, result and coverage SKU populations differ")
    combined = {}
    for sku in product_by_sku:
        result = result_by_sku.get(sku)
        state = coverage_by_sku[sku].get("status")
        if result is None:
            if state != "NOT_ATTEMPTED":
                raise ValueError(f"TV PDP result is missing for {sku}")
            result = {"exact_sku": sku, "status": state, "error": "PDP collection was not attempted"}
        if result.get("status") != state or state not in ("VERIFIED_EXACT_IDENTITY", "FAILED", "NOT_ATTEMPTED"):
            raise ValueError(f"TV PDP result status disagrees with coverage for {sku}")
        combined[sku] = result
    return combined, product_by_sku, summary


def epa_inputs(epa_root, expected_run_id):
    root = Path(epa_root)
    summary = read_json(root / "capture-summary.json")
    raw = (root / "samsung-current-rows.json").read_bytes()
    if (summary.get("status") != "PASS" or summary.get("dataset_id") != "pd96-rr3d"
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
    if (review.get("status") != "PASS" or review.get("contract") != "G3_TV_ENERGYGUIDE_RAW_CANDIDATE_REVIEW_V1"
            or str(review.get("retrieval_run_id")) != str(args.epa_run_id)):
        raise ValueError("TV raw-label review is not bound to the same EPA/PDF retrieval run")
    pdp_by_sku, product_by_sku, pdp_summary = collection_inputs(args.collection_root, args.collection_run_id)
    if str(review.get("collection_run_id")) != str(args.collection_run_id):
        raise ValueError("TV review table is not bound to the same PDP collection run")
    epa_rows, epa_summary = epa_inputs(args.epa_root, args.epa_run_id)
    population = sorted(product_by_sku)
    if review.get("sku_population_count") != len(population):
        raise ValueError("TV PDP and label-review SKU populations differ")

    label_by_sku = {sku: [] for sku in population}
    for entry in review.get("entries", []):
        models = entry.get("model_candidates_raw", [])
        energies = [row for row in entry.get("annual_energy_candidates_raw", [])
                    if row.get("role") == "ANNUAL_CAPTION_CONTEXT"]
        for sku in entry.get("exact_skus", []):
            if sku not in label_by_sku:
                raise ValueError("TV label review contains SKU outside the PDP population")
            label_by_sku[sku].append({"pdf_sha256": entry.get("pdf_sha256"),
                                      "model_candidates_raw": models,
                                      "annual_energy_candidates_raw": energies,
                                      "capacity_candidates_raw": entry.get("capacity_candidates_raw", []),
                                      "review_flags": entry.get("review_flags", [])})
    no_review_document = set(review.get("skus_without_review_document", review.get("skus_without_support_document", [])))
    unreadable_by_sku = {}
    for item in review.get("unreadable_documents", []):
        unreadable_by_sku.setdefault(item.get("exact_sku"), []).append(item)
    if any(not label_by_sku[sku] for sku in population if sku not in no_review_document):
        raise ValueError("A SKU with a Support-declared document is missing its label review record")

    table = []
    for sku in population:
        pdp = pdp_by_sku[sku]
        pdp_facts = pdp.get("pdp_facts_raw", {})
        product = product_by_sku[sku]
        listing = product.get("source_claim_listing_raw", {})
        label_records = label_by_sku[sku]
        unreadable_labels = unreadable_by_sku.get(sku, [])
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

        pdp_power = []
        for field in pdp_facts.get("power_consumption_raw", []):
            pdp_power.append({"value_raw": field.get("value"), "watts_decimal_candidate": extract_watts(field.get("value")),
                              "field_name_raw": field.get("name"), "field_group_raw": field.get("group")})

        epa_matches = []
        epa_normalized_matches = []
        for row in epa_rows:
            model_raw = row.get("model_number")
            match = model_prefix_match(model_raw, sku)
            if match:
                epa_matches.append({**match, "pd_id": row.get("pd_id"), "model_number_raw": model_raw,
                                    "annual_energy_raw": row.get("reported_annual_energy_consumption_kwh"),
                                    "annual_energy_kwh_decimal_candidate": decimal_value(row.get("reported_annual_energy_consumption_kwh")),
                                    "markets_raw": row.get("markets"), "market_scope_candidate": us_market_scope(row.get("markets")),
                                    "date_qualified_raw": row.get("date_qualified"),
                                    "diagonal_viewable_screen_size_inches_raw": row.get("diagonal_viewable_screen_size_inches"),
                                    "power_consumption_in_on_mode_watts_raw": row.get("power_consumption_in_on_mode_watts"),
                                    "federal_test_power_watts_raw": row.get("reported_on_mode_power_per_the_federal_test_procedure_watts")})
            normalized_match = normalized_pattern_match(model_raw, sku)
            if normalized_match:
                epa_normalized_matches.append({**normalized_match, "pd_id": row.get("pd_id"),
                                               "annual_energy_raw": row.get("reported_annual_energy_consumption_kwh"),
                                               "markets_raw": row.get("markets"),
                                               "strict_match_already_found": bool(match)})

        epa_us_matches = [row for row in epa_matches if row["market_scope_candidate"] == "US_MARKET_LISTED"]
        matched_label_hashes = {row.get("pdf_sha256") for row in label_matches}
        label_kwh = [row["kwh_decimal_candidate"] for row in label_energies
                     if row.get("pdf_sha256") in matched_label_hashes]
        epa_kwh = [decimal_value(row.get("annual_energy_raw")) for row in epa_us_matches]
        label_epa_energy = compare_single_candidates(label_kwh, epa_kwh,
                                                     "NO_LABEL_ANNUAL_KWH_CANDIDATE",
                                                     "NO_EXACT_US_EPA_ANNUAL_KWH_CANDIDATE")
        if unreadable_labels and not label_records:
            label_epa_energy["status"] = "LABEL_NOT_ACCESSIBLE_HIGH"
        elif label_records and not label_matches:
            label_epa_energy["status"] = "LABEL_MODEL_PATTERN_UNMATCHED"
        epa_on_mode_watts = [epa_watts(row.get("power_consumption_in_on_mode_watts_raw"))
                             for row in epa_us_matches]
        epa_federal_watts = [epa_watts(row.get("federal_test_power_watts_raw"))
                             for row in epa_us_matches]
        pdp_typical_watts = [row["watts_decimal_candidate"] for row in pdp_power
                             if "Typical" in str(row.get("field_name_raw"))]
        pdp_epa_typical_on_mode = compare_single_candidates(pdp_typical_watts, epa_on_mode_watts,
                                                             "NO_PDP_TYPICAL_WATTS",
                                                             "NO_EXACT_US_EPA_ON_MODE_WATTS")
        pdp_epa_typical_federal = compare_single_candidates(pdp_typical_watts, epa_federal_watts,
                                                             "NO_PDP_TYPICAL_WATTS",
                                                             "NO_EXACT_US_EPA_FEDERAL_TEST_WATTS")
        finding_candidates = ([{"severity": "HIGH", "issue_code": "ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE",
                                "control": "ENERGYGUIDE_READABILITY", "state": "NOT_ACCESSIBLE",
                                "evidence": unreadable_labels}] if unreadable_labels else [])
        if (label_epa_energy["status"] == "VALUES_DIFFER" and label_matches and epa_us_matches):
            finding_candidates.append({"severity": "MEDIUM", "issue_code": "ENERGYGUIDE_EPA_ANNUAL_ENERGY_DIFFERENCE_CANDIDATE",
                                        "control": "ANNUAL_ENERGY", "evidence": label_epa_energy})
        source_kwh_values = {"PDP": sorted(set(x["kwh_decimal_candidate"] for x in pdp_energies if x["kwh_decimal_candidate"])),
                             "LABEL": sorted(set(label_epa_energy["left_candidates"])),
                             "EPA_US_MARKET_CANDIDATE": sorted(set(label_epa_energy["right_candidates"]))}
        table.append({"exact_sku": sku, "pdp_title_raw": listing.get("modelName"),
                      "pdp_collection_status": pdp.get("status"), "pdp_collection_error": pdp.get("error"),
                      "pdp_identity_contract": pdp.get("identity_contract"),
                      "pdp_source_provenance": {"final_url_raw": pdp.get("final_url"),
                                                "snapshot_sha256": pdp.get("snapshot_sha256"),
                                                "bridge_sha256": (pdp.get("bridge") or {}).get("sha256")},
                      "pdp_energy_candidates_raw": pdp_energies,
                      "pdp_power_candidates_raw": pdp_power,
                      "label_document_count": len(label_records), "label_model_patterns_raw": label_patterns,
                      "label_document_accessibility": "NOT_ACCESSIBLE" if unreadable_labels and not label_records else "PARTIALLY_ACCESSIBLE" if unreadable_labels else "ACCESSIBLE" if label_records else "NO_LABEL_DOCUMENT_REVIEWED",
                      "label_unreadable_documents": unreadable_labels,
                      "finding_candidates": finding_candidates,
                      "label_prefix_matches": label_matches, "label_annual_energy_candidates_raw": label_energies,
                      "epa_current_model_matches": epa_matches,
                      "epa_match_count": len(epa_matches), "source_kwh_values": source_kwh_values,
                      "label_epa_annual_energy_comparison": label_epa_energy,
                      "pdp_typical_vs_epa_on_mode_power_comparison": pdp_epa_typical_on_mode,
                      "pdp_typical_vs_epa_federal_test_power_comparison": pdp_epa_typical_federal,
                      "epa_normalized_pattern_matches_diagnostic_only": epa_normalized_matches,
                      "epa_near_pattern_candidates_diagnostic_only": near_epa_patterns(sku, epa_rows) if not epa_matches else [],
                      "energy_comparison_candidate": label_epa_energy["status"],
                      "model_comparison": {"pdp": "EXACT_SKU_IDENTITY_VERIFIED" if pdp.get("status") == "VERIFIED_EXACT_IDENTITY" else "EXACT_SKU_IDENTITY_NOT_VERIFIED",
                                           "label": "ONE_OR_MORE_PREFIX_PATTERNS_MATCH" if label_matches else "NO_LABEL_PATTERN_MATCH",
                                           "epa_current": "ONE_OR_MORE_CURRENT_ROWS_MATCH" if epa_matches else "NO_CURRENT_EPA_MODEL_ROW_MATCH"},
                      "combo_routing": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"})

    report = {"contract": CONTRACT, "status": "PASS", "review_run_id": review.get("review_queue_run_id"),
              "collection_run_id": str(args.collection_run_id), "epa_capture_run_id": str(args.epa_run_id),
              "comparison_run_id": os.getenv("GITHUB_RUN_ID"), "git_sha": os.getenv("GITHUB_SHA"),
              "captured_at": datetime.now(timezone.utc).isoformat(), "population_count": len(population),
              "label_accessibility_counts": {"ACCESSIBLE": sum(not bool(unreadable_by_sku.get(sku)) and bool(label_by_sku[sku]) for sku in population),
                                             "NOT_ACCESSIBLE": sum(bool(unreadable_by_sku.get(sku)) and not label_by_sku[sku] for sku in population),
                                             "PARTIALLY_ACCESSIBLE": sum(bool(unreadable_by_sku.get(sku)) and bool(label_by_sku[sku]) for sku in population)},
              "epa_samsung_current_row_count": len(epa_rows),
              "model_pattern_contract": "Raw exact SKU is unchanged; each * consumes one A-Z/0-9 character from its beginning; any remaining exact-SKU suffix is retained verbatim and reported.",
              "scope": "Same-run TV source candidates are compared only across like units: label annual kWh vs EPA annual kWh, and PDP typical W vs EPA on-mode/federal-test W. EPA values require an explicit US market. Annual PDP kWh is reported separately when not published. HIGH unreadable-label and MEDIUM confirmed annual-energy-difference candidates are emitted; no other verdict or compliance assessment",
              "pdp_annual_energy_source_status": "NOT_PUBLISHED_IN_PDP_SPECS" if not any(row["pdp_energy_candidates_raw"] for row in table) else "PUBLISHED_CANDIDATES_PRESENT",
              "label_epa_annual_energy_counts": {name: sum(row["label_epa_annual_energy_comparison"]["status"] == name for row in table)
                         for name in ("EXACT_VALUE_MATCH", "VALUES_DIFFER", "MULTIPLE_VALUE_CANDIDATES",
                                      "NO_LABEL_ANNUAL_KWH_CANDIDATE", "NO_EXACT_US_EPA_ANNUAL_KWH_CANDIDATE",
                                      "LABEL_NOT_ACCESSIBLE_HIGH", "LABEL_MODEL_PATTERN_UNMATCHED")},
              "pdp_epa_power_counts": {name: sum(row["pdp_typical_vs_epa_on_mode_power_comparison"]["status"] == name for row in table)
                         for name in ("EXACT_VALUE_MATCH", "VALUES_DIFFER", "MULTIPLE_VALUE_CANDIDATES",
                                      "NO_PDP_TYPICAL_WATTS", "NO_EXACT_US_EPA_ON_MODE_WATTS")},
              "finding_candidate_counts": {name: sum(item["issue_code"] == name for row in table for item in row["finding_candidates"])
                                            for name in ("ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE",
                                                         "ENERGYGUIDE_EPA_ANNUAL_ENERGY_DIFFERENCE_CANDIDATE")},
              "rows": table}
    destination = Path(args.out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "source-comparison-candidates.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("## TV PDP / label / EPA comparison candidates\n\n")
            stream.write(f"Exact SKUs: **{len(population)}**; readable EnergyGuide PDFs: **{review.get('unique_pdf_count')}**; NOT_ACCESSIBLE HIGH candidates: **{report['finding_candidate_counts']['ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE']}**; label/EPA annual-kWh difference candidates: **{report['finding_candidate_counts']['ENERGYGUIDE_EPA_ANNUAL_ENERGY_DIFFERENCE_CANDIDATE']}**; EPA Samsung current rows captured: **{len(epa_rows)}**.\n\n")
            stream.write("PDP publishes typical/max/standby **W**, while the EnergyGuide publishes annual **kWh**. These are not compared as if they were the same quantity.\n\n")
            stream.write("| Exact SKU | PDP typical W | Label annual kWh | EPA annual kWh | Label/EPA status | PDP/EPA on-mode W |\n|---|---|---|---|---|---|\n")
            for row in table:
                label_cell = ("NOT_ACCESSIBLE — HIGH ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE"
                              if row["label_document_accessibility"] == "NOT_ACCESSIBLE"
                              else ", ".join(row["label_epa_annual_energy_comparison"]["left_candidates"]) or "—")
                epa_energy = ", ".join(row["label_epa_annual_energy_comparison"]["right_candidates"]) or "—"
                pdp_typical = ", ".join(x["watts_decimal_candidate"] for x in row["pdp_power_candidates_raw"]
                                         if "Typical" in str(x.get("field_name_raw")) and x["watts_decimal_candidate"]) or "—"
                epa_watts = ", ".join(row["pdp_typical_vs_epa_on_mode_power_comparison"]["right_candidates"]) or "—"
                cells = [row["exact_sku"], pdp_typical, label_cell, epa_energy,
                         row["label_epa_annual_energy_comparison"]["status"], epa_watts]
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
                      "epa_samsung_current_row_count": len(epa_rows),
                      "label_epa_annual_energy_counts": report["label_epa_annual_energy_counts"],
                      "pdp_epa_power_counts": report["pdp_epa_power_counts"],
                      "finding_candidate_counts": report["finding_candidate_counts"],
                      "comparison_table": table}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

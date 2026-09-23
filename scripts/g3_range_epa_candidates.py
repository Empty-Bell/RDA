"""Join exact-SKU Range claims to current EPA pattern candidates; no assessment."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from epa_only_rules import model_pattern_candidate

COLLECTION_CONTRACT = "G3_RANGE_EXACT_SKU_PDP_V1"
EPA_CONTRACT = "G3_RANGE_EPA_CURRENT_SOURCE_V1"
REPORT_CONTRACT = "G3_RANGE_EPA_SOURCE_CANDIDATES_V1"
DATASET = "m6gi-ng33"


def read_json(path):
    return json.loads(Path(path).read_bytes())


def load_collection(root, run_id):
    root = Path(root)
    summary = read_json(root / "collection-summary.json")
    if (summary.get("status") != "PASS"
            or summary.get("contract") != COLLECTION_CONTRACT
            or str(summary.get("collection_run_id")) != str(run_id)):
        raise ValueError("Range PDP collection is not the requested successful contract/run")
    products = read_json(root / "products.json")
    expected = summary.get("coverage", {}).get("population_count")
    paths = sorted(root.glob("pdp/*/result.json"))
    if not isinstance(expected, int) or len(products) != expected or len(paths) != expected:
        raise ValueError("Range PDP collection is incomplete")
    product_skus = [row.get("exact_sku") for row in products]
    if len(set(product_skus)) != expected:
        raise ValueError("Range product population has duplicate exact SKUs")
    claims = {}
    facts_by_sku = {}
    for path in paths:
        row = read_json(path)
        sku = row.get("exact_sku")
        if sku not in set(product_skus) or row.get("status") != "VERIFIED_EXACT_IDENTITY":
            raise ValueError("Range PDP result is failed, duplicate, or outside population")
        claim = row.get("energy_star_claim_sources_raw")
        if not isinstance(claim, dict) or claim.get("exact_sku") != sku:
            raise ValueError("Range claim evidence lacks exact-SKU provenance")
        snapshot_path = path.with_name("snapshot.json")
        snapshot_raw = snapshot_path.read_bytes()
        if hashlib.sha256(snapshot_raw).hexdigest() != row.get("snapshot_sha256"):
            raise ValueError("Range PDP snapshot hash mismatch")
        snapshot = json.loads(snapshot_raw)
        if snapshot.get("target_sku") != sku:
            raise ValueError("Range PDP snapshot lacks exact-SKU provenance")
        if sku in claims:
            raise ValueError("Range PDP result contains duplicate SKU")
        facts_by_sku[sku] = row.get("pdp_facts_raw", {})
        claims[sku] = {**claim,
                       "pdp_logo_inspection_raw": snapshot.get("primary_logo_inspection"),
                       "pdp_spec_surface_inspection_raw": snapshot.get("spec_surface_inspection"),
                       "pdp_visible_spec_energy_star_rows_raw": snapshot.get("visible_spec_energy_star_rows", [])}
    if set(claims) != set(product_skus):
        raise ValueError("Range PDP result set differs from the exact SKU population")
    return claims, facts_by_sku, products, summary


def load_epa(root, run_id):
    root = Path(root)
    summary = read_json(root / "capture-summary.json")
    raw = (root / "samsung-current-rows.json").read_bytes()
    if (summary.get("status") != "PASS" or summary.get("contract") != EPA_CONTRACT
            or summary.get("dataset_id") != DATASET
            or str(summary.get("capture_run_id")) != str(run_id)
            or hashlib.sha256(raw).hexdigest() != summary.get("rows_sha256")):
        raise ValueError("Range EPA source capture identity/hash is invalid")
    rows = json.loads(raw)
    if not isinstance(rows, list) or len(rows) != summary.get("row_count"):
        raise ValueError("Range EPA rows do not match capture summary")
    if any(not isinstance(row, dict) or not row.get("source_row_id")
           or not row.get("pd_id") or not row.get("model_number") for row in rows):
        raise ValueError("Range EPA row lacks source/model identity")
    return rows, summary


def project_candidate(row, candidate):
    return {
        "source_row_id": row.get("source_row_id"),
        "pd_id": row.get("pd_id"),
        "brand_name_raw": row.get("brand_name"),
        "model_number_raw": row.get("model_number"),
        "model_name_raw": row.get("model_name"),
        "additional_model_information_raw": row.get("additional_model_information"),
        "product_type_raw": row.get("product_type"),
        "cooking_top_technology_raw": row.get("cooking_top_technology"),
        "markets_raw": row.get("markets"),
        "date_certified_raw": row.get("date_certified"),
        "annual_energy_consumption_kwh_yr_raw": row.get("annual_energy_consumption_kwh_yr"),
        "low_power_mode_energy_consumption_oven_kwh_yr_raw": row.get("low_power_mode_energy_consumption_oven_kwh_yr"),
        "low_power_mode_energy_consumption_cooking_top_kwh_yr_raw": row.get("low_power_mode_energy_consumption_cooking_top_kwh_yr"),
        "model_pattern_candidate": candidate,
    }


def build(collection_root, collection_run_id, epa_root, epa_run_id, output):
    claims, facts_by_sku, products, collection_summary = load_collection(collection_root, collection_run_id)
    epa_rows, epa_summary = load_epa(epa_root, epa_run_id)
    records = []
    observed_fuel = Counter()
    candidate_count = other_type_count = 0
    for product in sorted(products, key=lambda row: row["exact_sku"]):
        sku = product["exact_sku"]
        spec_fields = facts_by_sku.get(sku, {}).get("spec_fields_raw", [])
        fuel_facts = [field for field in spec_fields if any(token in str(field.get("name", "")).casefold()
                       for token in ("fuel", "cooktop type", "cooking type"))]
        for fact in fuel_facts:
            observed_fuel[(str(fact.get("name")), str(fact.get("value")))] += 1
        range_candidates, other_types = [], []
        for source in epa_rows:
            candidate = model_pattern_candidate(source.get("model_number"), sku)
            if candidate is None:
                continue
            row = project_candidate(source, candidate)
            if str(source.get("product_type", "")).strip().casefold() == "range":
                range_candidates.append(row)
            else:
                other_types.append(row)
        candidate_count += len(range_candidates)
        other_type_count += len(other_types)
        records.append({
            "exact_sku": sku,
            "pdp_product_facts_raw": {"fuel_or_cooktop_facts": fuel_facts,
                                       "all_spec_fields": spec_fields},
            "energy_star_claim_sources_raw": claims[sku],
            "range_epa_pattern_candidates": range_candidates,
            "same_pattern_non_range_epa_rows": other_types,
            "applicability": "NOT_EVALUATED",
            "certification_identity": "NOT_EVALUATED",
            "publication_consistency": "NOT_EVALUATED",
            "assessment": "NOT_EVALUATED",
        })
    report = {
        "contract": REPORT_CONTRACT,
        "status": "SOURCE_CANDIDATES_READY",
        "source_validation": "PASS",
        "collection_run_id": str(collection_run_id),
        "epa_capture_run_id": str(epa_run_id),
        "git_sha": os.getenv("GITHUB_SHA"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "population_count": len(records),
        "epa_samsung_row_count": len(epa_rows),
        "range_pattern_candidate_row_count": candidate_count,
        "skus_with_range_pattern_candidates": sum(bool(row["range_epa_pattern_candidates"]) for row in records),
        "skus_without_range_pattern_candidates": sum(not row["range_epa_pattern_candidates"] for row in records),
        "skus_with_only_non_range_product_candidates": sum(
            bool(row["same_pattern_non_range_epa_rows"]) and not row["range_epa_pattern_candidates"]
            for row in records),
        "same_pattern_non_range_row_count": other_type_count,
        "fuel_and_cooktop_spec_observations": [
            {"name": name, "value": value, "sku_observation_count": count}
            for (name, value), count in sorted(observed_fuel.items())],
        "source_hashes": {"epa_rows_sha256": epa_summary["rows_sha256"],
                          "collection_run_id": str(collection_run_id)},
        "model_candidate_contract": "Literal equality or positional pattern candidate; '*' consumes one A-Z/0-9 position. A candidate is not a certification match.",
        "assessment_contract": "No applicability, certification identity, publication consistency, severity, or compliance rule is applied.",
        "scope": "Range PDP claims and raw EPA electric-cooking model-pattern candidates only. EPA product_type and market are retained as evidence; no legal applicability conclusion is made.",
        "collection_contract": collection_summary["contract"],
        "records": records,
    }
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "range-epa-source-candidates.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    step_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary:
        with Path(step_summary).open("a", encoding="utf-8") as stream:
            stream.write("## Range EPA source candidates\n\n")
            stream.write(f"PDP exact SKUs: **{len(records)}**; EPA Samsung rows: **{len(epa_rows)}**; EPA Range pattern candidates: **{candidate_count}**. No compliance decisions were run.\n\n")
            stream.write("| Exact SKU | PDP fuel facts | PLP flag | PDP logo | Spec certification | EPA Range candidates | Other product-type matches |\n|---|---:|---|---:|---:|---:|---:|\n")
            for row in records:
                claim = row["energy_star_claim_sources_raw"]
                cells = [row["exact_sku"], len(row["pdp_product_facts_raw"]["fuel_or_cooktop_facts"]),
                         claim.get("plp_energy_star_flag_raw"),
                         len(claim.get("rendered_attributed_badges_raw", [])),
                         len(claim.get("pdp_visible_spec_energy_star_rows_raw", [])),
                         len(row["range_epa_pattern_candidates"]),
                         len(row["same_pattern_non_range_epa_rows"])]
                stream.write("| " + " | ".join(str(value if value is not None else "(not observed)").replace("|", "\\|") for value in cells) + " |\n")
            stream.write("\nEPA candidates are evidence leads only. Range applicability and every audit outcome remain NOT_EVALUATED.\n")
    examples = [{"sku": row["exact_sku"],
                 "pdp_fuel_facts": row["pdp_product_facts_raw"]["fuel_or_cooktop_facts"],
                 "range_epa_patterns": [{"model": candidate["model_number_raw"],
                                         "markets": candidate["markets_raw"]}
                                        for candidate in row["range_epa_pattern_candidates"]],
                 "other_epa_product_types": sorted({str(candidate["product_type_raw"])
                                                     for candidate in row["same_pattern_non_range_epa_rows"]})}
                for row in records if row["range_epa_pattern_candidates"]
                or row["same_pattern_non_range_epa_rows"]]
    potential_electric_unmatched = []
    for row in records:
        if row["range_epa_pattern_candidates"]:
            continue
        fuel_facts = row["pdp_product_facts_raw"]["fuel_or_cooktop_facts"]
        fuel_values = {str(fact.get("value", "")).strip().casefold()
                       for fact in fuel_facts if str(fact.get("name", "")).strip().casefold() == "fuel type"}
        if fuel_values & {"electric", "induction"}:
            claim = row["energy_star_claim_sources_raw"]
            potential_electric_unmatched.append({
                "sku": row["exact_sku"],
                "fuel_facts": fuel_facts,
                "plp_energy_star_flag_raw": claim.get("plp_energy_star_flag_raw"),
                "pdp_rendered_logo_candidate_count": len(claim.get("rendered_attributed_badges_raw", [])),
                "pdp_visible_spec_claim_rows": claim.get("pdp_visible_spec_energy_star_rows_raw", []),
            })
    print(json.dumps({"status": report["status"], "source_validation": "PASS",
                      "population_count": len(records), "epa_samsung_rows": len(epa_rows),
                      "range_pattern_candidate_rows": candidate_count,
                      "skus_with_range_candidates": report["skus_with_range_pattern_candidates"],
                      "skus_without_range_candidates": report["skus_without_range_pattern_candidates"],
                      "skus_with_only_other_product_type_candidates": report["skus_with_only_non_range_product_candidates"],
                      "fuel_observations": report["fuel_and_cooktop_spec_observations"],
                      "candidate_examples": examples,
                      "electric_or_induction_without_epa_candidate": potential_electric_unmatched,
                      "applicability": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"},
                     ensure_ascii=False, sort_keys=True), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--collection-run-id", required=True)
    parser.add_argument("--epa-root", required=True)
    parser.add_argument("--epa-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build(args.collection_root, args.collection_run_id, args.epa_root,
          args.epa_run_id, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


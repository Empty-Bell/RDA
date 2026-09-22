"""Join Dryer PDP, label, and EPA source candidates without selecting or assessing."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re


CONTRACT = "G3_DRYER_SOURCE_CANDIDATE_JOIN_V1"
MODEL_PATTERN = re.compile(r"[A-Z0-9*/?./-]+\Z", re.I)


def read_json(path):
    return json.loads(Path(path).read_bytes())


def positional_prefix_candidate(pattern, exact_sku):
    """Return a transparent pattern inclusion candidate; never a decision."""
    if not isinstance(pattern, str) or not MODEL_PATTERN.fullmatch(pattern) or not isinstance(exact_sku, str):
        return None
    expression = "^" + "".join("[A-Z0-9]" if char == "*" else re.escape(char.upper()) for char in pattern)
    if not re.match(expression, exact_sku.upper()):
        return None
    return {"pattern_raw": pattern, "exact_sku_raw": exact_sku,
            "candidate_basis": "POSITIONAL_PREFIX_PATTERN_CANDIDATE; * = ONE A-Z/0-9 CHARACTER",
            "matched_prefix_raw": exact_sku[:len(pattern)],
            "remaining_sku_suffix_raw": exact_sku[len(pattern):]}


def load_collection(root, run_id):
    root = Path(root)
    summary = read_json(root / "collection-summary.json")
    if summary.get("status") != "PASS" or str(summary.get("collection_run_id")) != str(run_id):
        raise ValueError("Dryer PDP collection is not the requested successful run")
    products = read_json(root / "products.json")
    results = [read_json(p) for p in sorted(root.glob("pdp/*/result.json"))]
    skus = [row.get("exact_sku") for row in results]
    if len(results) != summary.get("coverage", {}).get("population_count") or len(set(skus)) != len(skus):
        raise ValueError("Dryer PDP collection population is incomplete or duplicated")
    if any(row.get("status") != "VERIFIED_EXACT_IDENTITY" for row in results):
        raise ValueError("Dryer PDP collection includes an unverified exact SKU")
    product_map = {row.get("exact_sku"): row for row in products}
    if set(product_map) != set(skus):
        raise ValueError("Dryer PDP listing and result SKU populations differ")
    return {row["exact_sku"]: row for row in results}, product_map, summary


def load_epa(root, run_id):
    root = Path(root)
    summary = read_json(root / "capture-summary.json")
    raw = (root / "samsung-current-rows.json").read_bytes()
    if (summary.get("status") != "PASS" or summary.get("dataset_id") != "t9u7-4d2j"
            or str(summary.get("capture_run_id")) != str(run_id)
            or hashlib.sha256(raw).hexdigest() != summary.get("rows_sha256")):
        raise ValueError("Dryer EPA rows are not the requested hash-verified capture")
    rows = json.loads(raw)
    if not isinstance(rows, list) or len(rows) != summary.get("row_count"):
        raise ValueError("Dryer EPA source row count does not match capture metadata")
    return rows


def join_candidates(review_root, collection_root, collection_run_id, epa_root, epa_run_id, output):
    review = read_json(Path(review_root) / "review-queue.json")
    if (review.get("status") != "PASS" or review.get("contract") != "G3_DRYER_ENERGYGUIDE_RAW_CANDIDATE_REVIEW_V1"
            or str(review.get("retrieval_run_id")) != str(epa_run_id)):
        raise ValueError("Dryer label review is not bound to the requested source-capture run")
    if str(review.get("collection_run_id")) != str(collection_run_id):
        raise ValueError("Dryer label review and PDP collection do not share a collection run")
    pdps, products, summary = load_collection(collection_root, collection_run_id)
    epa_rows = load_epa(epa_root, epa_run_id)
    population = sorted(pdps)
    if review.get("sku_population_count") != len(population):
        raise ValueError("Dryer review queue and PDP SKU populations differ")
    labels = {sku: [] for sku in population}
    for entry in review.get("entries", []):
        for sku in entry.get("exact_skus", []):
            if sku not in labels:
                raise ValueError("Dryer label review links a SKU outside the exact PDP population")
            labels[sku].append({"pdf_sha256": entry.get("pdf_sha256"),
                                "model_candidates_raw": entry.get("model_candidates_raw", []),
                                "annual_energy_candidates_raw": entry.get("annual_energy_candidates_raw", []),
                                "capacity_candidates_raw": entry.get("capacity_candidates_raw", []),
                                "review_flags": entry.get("review_flags", [])})
    no_docs = set(review.get("skus_without_support_document", []))
    if no_docs - set(population):
        raise ValueError("Dryer review queue no-document list contains an unknown SKU")
    if any(not labels[sku] for sku in population if sku not in no_docs):
        raise ValueError("Dryer Support-declared document is missing from the label review queue")

    output_rows = []
    for sku in population:
        pdp = pdps[sku]
        facts = pdp.get("pdp_facts_raw", {})
        listing = products[sku].get("source_claim_listing_raw", {})
        label_docs = []
        for document in labels[sku]:
            models = document["model_candidates_raw"]
            label_docs.append({**document, "model_inclusion_candidates": [candidate for model in models
                                  if (candidate := positional_prefix_candidate(model.get("value_raw"), sku))]})
        epa_matches = []
        for row in epa_rows:
            candidate = positional_prefix_candidate(row.get("model_number"), sku)
            if candidate:
                epa_matches.append({**candidate, "source_row_id": row.get("source_row_id"),
                                    "pd_id": row.get("pd_id"), "model_number_raw": row.get("model_number"),
                                    "markets_raw": row.get("markets"), "date_qualified_raw": row.get("date_qualified"),
                                    "type_raw": row.get("type"), "product_type_raw": row.get("product_type"),
                                    "vented_or_ventless_raw": row.get("vented_or_ventless"),
                                    "annual_energy_kwh_yr_raw": row.get("estimated_annual_energy_use_kwh_yr"),
                                    "combined_energy_factor_cef_raw": row.get("combined_energy_factor_cef"),
                                    "drum_capacity_cu_ft_raw": row.get("drum_capacity_cu_ft")})
        output_rows.append({"exact_sku": sku, "pdp_title_raw": listing.get("modelName"),
                            "pdp_identity": pdp.get("identity_contract"),
                            "pdp_energy_specs_raw": facts.get("energy_consumption_raw", []),
                            "pdp_drying_capacity_raw": facts.get("capacity_raw", []),
                            "label_support_document_state": "DOCUMENT_REVIEWED" if label_docs else "NO_SUPPORT_DOCUMENT_DECLARED",
                            "label_documents": label_docs, "epa_model_pattern_candidates": epa_matches,
                            "epa_model_candidate_count": len(epa_matches),
                            "numeric_comparison": "NOT_EVALUATED",
                            "family_routing": "NOT_EVALUATED",
                            "assessment": "NOT_EVALUATED"})
    report = {"contract": CONTRACT, "status": "PASS", "collection_run_id": str(collection_run_id),
              "epa_capture_run_id": str(epa_run_id), "review_run_id": review.get("review_queue_run_id"),
              "comparison_run_id": os.getenv("GITHUB_RUN_ID"), "git_sha": os.getenv("GITHUB_SHA"),
              "captured_at": datetime.now(timezone.utc).isoformat(), "population_count": len(population),
              "epa_samsung_current_row_count": len(epa_rows), "sku_without_support_document_count": len(no_docs),
              "model_candidate_contract": "Positional prefix candidate only: each * consumes one A-Z/0-9 character; remaining exact-SKU suffix is preserved. Candidate is not a match decision.",
              "scope": "Same-run exact-SKU PDP, Support-label, and EPA source observations; raw source candidates only; no value selection, family routing, numeric comparison, pass/fail, severity, or compliance assessment",
              "rows": output_rows}
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "source-candidates.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    step_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary:
        with Path(step_summary).open("a", encoding="utf-8") as stream:
            stream.write("## Dryer PDP / EnergyGuide / EPA source candidates\n\n")
            stream.write(f"Exact PDP SKUs: **{len(population)}**; EPA Samsung rows: **{len(epa_rows)}**; SKUs without a Support label: **{len(no_docs)}**. No selection, comparison, or assessment was made.\n\n")
            stream.write("| Exact SKU | PDP title | Label model candidates | Label annual-kWh candidates | EPA model rows / annual kWh / CEF | Label docs |\n|---|---|---|---|---|---:|\n")
            for row in output_rows:
                label_models = "; ".join(", ".join(sorted({m.get("value_raw", "") for m in doc["model_candidates_raw"] if m.get("value_raw")})) or "no model candidate" for doc in row["label_documents"]) or "none"
                label_energy = "; ".join(", ".join(sorted({e.get("value_raw", "") for e in doc["annual_energy_candidates_raw"] if e.get("value_raw")})) or "no annual-kWh candidate" for doc in row["label_documents"]) or "none"
                epa = "; ".join(f"{x['model_number_raw']} / {x['annual_energy_kwh_yr_raw']} / CEF {x['combined_energy_factor_cef_raw']}" for x in row["epa_model_pattern_candidates"]) or "no positional candidate"
                cells = [row["exact_sku"], row["pdp_title_raw"] or "", label_models, label_energy, epa, str(len(row["label_documents"]))]
                stream.write("| " + " | ".join(str(x).replace("|", "\\|").replace("\n", " ") for x in cells) + " |\n")
    print(json.dumps({"status": "PASS", "population_count": len(population), "epa_row_count": len(epa_rows),
                      "skus_without_support_document": len(no_docs),
                      "epa_candidate_rows": sum(row["epa_model_candidate_count"] for row in output_rows),
                      "numeric_comparison": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"}, sort_keys=True), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", required=True)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--collection-run-id", required=True)
    parser.add_argument("--epa-root", required=True)
    parser.add_argument("--epa-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    join_candidates(args.review_root, args.collection_root, args.collection_run_id,
                    args.epa_root, args.epa_run_id, args.out)


if __name__ == "__main__":
    main()

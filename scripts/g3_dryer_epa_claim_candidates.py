"""Join Dryer ENERGY STAR claim observations to EPA model-pattern candidates only."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from epa_only_rules import model_pattern_candidate

CONTRACT = "G3_DRYER_EPA_CLAIM_CANDIDATES_V1"
DATASETS = {"dryer": "t9u7-4d2j", "combo": "9jai-gs6t"}


def read_json(path):
    return json.loads(Path(path).read_bytes())


def positional_candidate(pattern, exact_sku):
    """Compatibility wrapper around the shared EPA-only positional matcher."""
    return model_pattern_candidate(pattern, exact_sku)


def load_collection(root, run_id):
    root = Path(root)
    summary = read_json(root / "collection-summary.json")
    if (summary.get("status") != "PASS"
            or summary.get("contract") != "G3_DRYER_EXACT_SKU_PDP_V1"
            or str(summary.get("collection_run_id")) != str(run_id)):
        raise ValueError("Dryer PDP collection is not the requested successful contract/run")
    expected = summary.get("coverage", {}).get("population_count")
    products = read_json(root / "products.json")
    results = [read_json(path) for path in sorted(root.glob("pdp/*/result.json"))]
    product_skus = [row.get("exact_sku") for row in products]
    result_skus = [row.get("exact_sku") for row in results]
    if (not isinstance(expected, int) or len(products) != expected or len(results) != expected
            or len(set(product_skus)) != expected or set(product_skus) != set(result_skus)):
        raise ValueError("Dryer PDP collection does not cover one exact result per population SKU")
    if any(row.get("status") != "VERIFIED_EXACT_IDENTITY" for row in results):
        raise ValueError("Dryer PDP collection includes a failed or unattempted SKU")
    claims = {}
    for result_path, row in zip(sorted(root.glob("pdp/*/result.json")), results):
        sku = row["exact_sku"]
        claim = row.get("energy_star_claim_sources_raw")
        if not isinstance(claim, dict) or claim.get("exact_sku") != sku:
            raise ValueError("Dryer claim observations lack exact-SKU provenance")
        snapshot_path = result_path.with_name("snapshot.json")
        snapshot_raw = snapshot_path.read_bytes()
        if hashlib.sha256(snapshot_raw).hexdigest() != row.get("snapshot_sha256"):
            raise ValueError("Dryer PDP DOM inspection hash does not match its result")
        snapshot = json.loads(snapshot_raw)
        if snapshot.get("target_sku") != sku:
            raise ValueError("Dryer PDP DOM inspection lacks exact-SKU provenance")
        claims[sku] = {**claim,
                       "pdp_logo_inspection_raw": snapshot.get("primary_logo_inspection"),
                       "pdp_spec_surface_inspection_raw": snapshot.get("spec_surface_inspection"),
                       "pdp_visible_spec_energy_star_rows_raw": snapshot.get("visible_spec_energy_star_rows", [])}
    return claims, summary


def load_epa(root, run_id, family):
    root = Path(root)
    summary = read_json(root / "capture-summary.json")
    rows_raw = (root / "samsung-current-rows.json").read_bytes()
    if (summary.get("status") != "PASS" or summary.get("dataset_id") != DATASETS[family]
            or str(summary.get("capture_run_id")) != str(run_id)
            or hashlib.sha256(rows_raw).hexdigest() != summary.get("rows_sha256")):
        raise ValueError(f"EPA {family} capture identity/hash is invalid")
    rows = json.loads(rows_raw)
    if not isinstance(rows, list) or len(rows) != summary.get("row_count"):
        raise ValueError(f"EPA {family} row count differs from its capture summary")
    if any(not isinstance(row, dict) or not row.get("model_number")
           or not row.get("source_row_id") or not row.get("pd_id") for row in rows):
        raise ValueError(f"EPA {family} row is missing model or source identity")
    return rows, summary


def project_epa_candidate(row, candidate, family):
    common = {"source_row_id": row.get("source_row_id"), "pd_id": row.get("pd_id"),
              "model_number_raw": row.get("model_number"), "markets_raw": row.get("markets"),
              "date_qualified_raw": row.get("date_qualified"), "candidate": candidate}
    if family == "dryer":
        common.update(product_type_raw=row.get("product_type"), fuel_type_raw=row.get("type"),
                      vented_or_ventless_raw=row.get("vented_or_ventless"))
    else:
        common.update(special_type_raw=row.get("special_type"),
                      intended_market_raw=row.get("intended_market"))
    return common


def build_report(collection_root, collection_run_id, epa_root, epa_run_id,
                 combo_epa_root, combo_epa_run_id, output):
    claims, collection_summary = load_collection(collection_root, collection_run_id)
    epa_rows, epa_summary = load_epa(epa_root, epa_run_id, "dryer")
    combo_rows, combo_summary = load_epa(combo_epa_root, combo_epa_run_id, "combo")
    rows = []
    for sku in sorted(claims):
        dryer_candidates = []
        for source in epa_rows:
            candidate = positional_candidate(source.get("model_number"), sku)
            if candidate:
                dryer_candidates.append(project_epa_candidate(source, candidate, "dryer"))
        combo_candidates = []
        for source in combo_rows:
            candidate = positional_candidate(source.get("model_number"), sku)
            if candidate:
                combo_candidates.append(project_epa_candidate(source, candidate, "combo"))
        rows.append({"exact_sku": sku, "energy_star_claim_sources_raw": claims[sku],
                     "dryer_epa_model_pattern_candidates": dryer_candidates,
                     "combo_epa_model_pattern_candidates": combo_candidates,
                     "certification_matching": "NOT_EVALUATED",
                     "claim_consistency": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"})
    report = {
        "contract": CONTRACT, "status": "SOURCE_CANDIDATES_READY", "source_validation": "PASS",
        "collection_run_id": str(collection_run_id),
        "epa_capture_run_id": str(epa_run_id), "combo_epa_capture_run_id": str(combo_epa_run_id),
        "git_sha": os.getenv("GITHUB_SHA"), "captured_at": datetime.now(timezone.utc).isoformat(),
        "population_count": len(rows), "dryer_epa_row_count": len(epa_rows),
        "combo_epa_row_count": len(combo_rows),
        "source_hashes": {"collection_run_id": str(collection_run_id),
                          "dryer_epa_rows_sha256": epa_summary["rows_sha256"],
                          "combo_epa_rows_sha256": combo_summary["rows_sha256"]},
        "model_candidate_contract": "Literal equality or positional prefix candidate; each * consumes one A-Z/0-9 character. Candidate is not certification identity.",
        "scope": "Dryer ENERGY STAR claim observations and EPA model-pattern candidates only; no EnergyGuide data, value comparison, match decision, severity, or compliance assessment.",
        "collection_contract": collection_summary["contract"], "rows": rows,
    }
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "epa-claim-candidates.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Dryer EPA ENERGY STAR claim-source candidates\n\n")
            stream.write(f"Exact PDP SKUs: **{len(rows)}**; EPA dryer rows: **{len(epa_rows)}**; EPA combo rows: **{len(combo_rows)}**. Model candidates are not matches, and all claims remain unassessed.\n\n")
            stream.write("| Exact SKU | PLP raw flag | PDP spec claims | PDP attributed logo candidates | Dryer EPA candidates | Combo EPA candidates |\n|---|---|---:|---:|---:|---:|\n")
            for row in rows:
                claim = row["energy_star_claim_sources_raw"]
                plp = claim.get("plp_energy_star_flag_raw")
                specs = claim.get("pdp_spec_energy_star_claim_raw", [])
                badges = claim.get("rendered_attributed_badges_raw", [])
                cells = [row["exact_sku"], plp, len(specs), len(badges),
                         len(row["dryer_epa_model_pattern_candidates"]),
                         len(row["combo_epa_model_pattern_candidates"])]
                stream.write("| " + " | ".join(str(value if value is not None else "(not observed)").replace("|", "\\|") for value in cells) + " |\n")
            stream.write("\nThis table reports source observations and possible model-pattern inclusions only. It does not classify a model as registered/unregistered or issue a finding.\n")
    print(json.dumps({"status": "SOURCE_CANDIDATES_READY", "source_validation": "PASS",
                      "population_count": len(rows),
                      "dryer_epa_rows": len(epa_rows), "combo_epa_rows": len(combo_rows),
                      "certification_matching": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"}, sort_keys=True))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--collection-run-id", required=True)
    parser.add_argument("--epa-root", required=True)
    parser.add_argument("--epa-run-id", required=True)
    parser.add_argument("--combo-epa-root", required=True)
    parser.add_argument("--combo-epa-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build_report(args.collection_root, args.collection_run_id, args.epa_root, args.epa_run_id,
                 args.combo_epa_root, args.combo_epa_run_id, args.out)


if __name__ == "__main__":
    main()

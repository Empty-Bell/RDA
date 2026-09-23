"""Join exact-SKU hood PDP claims to raw EPA ventilating-fan model candidates."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from epa_only_rules import model_pattern_candidate

COLLECTION_CONTRACT = "G3_HOOD_EXACT_SKU_PDP_V1"
EPA_CONTRACT = "G3_HOOD_EPA_CURRENT_SOURCE_V1"
REPORT_CONTRACT = "G3_HOOD_EPA_SOURCE_CANDIDATES_V1"
DATASET = "8dv7-nngq"


def read_json(path):
    return json.loads(Path(path).read_bytes())


def load_collection(root, run_id):
    root = Path(root)
    summary = read_json(root / "collection-summary.json")
    if (summary.get("status") != "PASS" or summary.get("contract") != COLLECTION_CONTRACT
            or str(summary.get("collection_run_id")) != str(run_id)):
        raise ValueError("Hood PDP collection is not the requested successful contract/run")
    products = read_json(root / "products.json")
    expected = summary.get("coverage", {}).get("population_count")
    paths = sorted(root.glob("pdp/*/result.json"))
    if not isinstance(expected, int) or len(products) != expected or len(paths) != expected:
        raise ValueError("Hood PDP collection is incomplete")
    skus = [row.get("exact_sku") for row in products]
    if len(set(skus)) != expected:
        raise ValueError("Hood population has duplicate exact SKUs")
    claims, facts = {}, {}
    for path in paths:
        row = read_json(path)
        sku = row.get("exact_sku")
        if sku not in set(skus) or row.get("status") != "VERIFIED_EXACT_IDENTITY":
            raise ValueError("Hood PDP result is failed, duplicate, or outside population")
        claim = row.get("energy_star_claim_sources_raw")
        if not isinstance(claim, dict) or claim.get("exact_sku") != sku:
            raise ValueError("Hood claim evidence lacks exact-SKU provenance")
        snapshot_raw = path.with_name("snapshot.json").read_bytes()
        if hashlib.sha256(snapshot_raw).hexdigest() != row.get("snapshot_sha256"):
            raise ValueError("Hood PDP snapshot hash mismatch")
        snapshot = json.loads(snapshot_raw)
        if snapshot.get("target_sku") != sku or sku in claims:
            raise ValueError("Hood snapshot identity is invalid or duplicated")
        claims[sku] = {**claim,
                       "pdp_logo_inspection_raw": snapshot.get("primary_logo_inspection"),
                       "pdp_spec_surface_inspection_raw": snapshot.get("spec_surface_inspection"),
                       "pdp_visible_spec_energy_star_rows_raw": snapshot.get("visible_spec_energy_star_rows", [])}
        facts[sku] = row.get("pdp_facts_raw", {})
    if set(claims) != set(skus):
        raise ValueError("Hood PDP result set differs from population")
    return products, claims, facts, summary


def load_epa(root, run_id):
    root = Path(root)
    summary = read_json(root / "capture-summary.json")
    raw = (root / "samsung-current-rows.json").read_bytes()
    if (summary.get("status") != "PASS" or summary.get("contract") != EPA_CONTRACT
            or summary.get("dataset_id") != DATASET or str(summary.get("capture_run_id")) != str(run_id)
            or hashlib.sha256(raw).hexdigest() != summary.get("rows_sha256")):
        raise ValueError("Hood EPA capture identity/hash is invalid")
    rows = json.loads(raw)
    if not isinstance(rows, list) or len(rows) != summary.get("row_count"):
        raise ValueError("Hood EPA rows do not match capture summary")
    if any(not isinstance(row, dict) or not row.get("source_row_id") or not row.get("pd_id")
           or not row.get("model_number") for row in rows):
        raise ValueError("EPA row lacks source/model identity")
    return rows, summary


def project_candidate(row, candidate):
    keep = ("source_row_id", "pd_id", "brand_name", "model_number", "model_name", "unit_type",
            "markets", "date_qualified", "airflow_1_cfm", "efficacy_1_cfm_w", "airflow_2_cfm",
            "efficacy_2_cfm_w", "airflow_3_cfm", "efficacy_3_cfm_w", "sound_level_sones")
    return {f"{key}_raw": row.get(key) for key in keep} | {"model_pattern_candidate": candidate}


def build(collection_root, collection_run_id, epa_root, epa_run_id, output):
    products, claims, facts, collection = load_collection(collection_root, collection_run_id)
    epa_rows, epa = load_epa(epa_root, epa_run_id)
    records, type_counts = [], Counter()
    for product in sorted(products, key=lambda row: row["exact_sku"]):
        sku = product["exact_sku"]
        candidates = []
        for source in epa_rows:
            matched = model_pattern_candidate(source.get("model_number"), sku)
            if matched is None:
                continue
            item = project_candidate(source, matched)
            candidates.append(item)
            type_counts[str(source.get("unit_type") or "(blank)")] += 1
        records.append({"exact_sku": sku, "pdp_product_facts_raw": facts.get(sku, {}),
                        "energy_star_claim_sources_raw": claims[sku],
                        "epa_ventilating_fan_pattern_candidates": candidates,
                        "applicability": "NOT_EVALUATED", "certification_identity": "NOT_EVALUATED",
                        "publication_consistency": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"})
    candidate_rows = sum(len(row["epa_ventilating_fan_pattern_candidates"]) for row in records)
    report = {"contract": REPORT_CONTRACT, "status": "SOURCE_CANDIDATES_READY", "source_validation": "PASS",
              "collection_run_id": str(collection_run_id), "epa_capture_run_id": str(epa_run_id),
              "git_sha": os.getenv("GITHUB_SHA"), "captured_at": datetime.now(timezone.utc).isoformat(),
              "population_count": len(records), "epa_samsung_row_count": len(epa_rows),
              "epa_model_pattern_candidate_row_count": candidate_rows,
              "skus_with_pattern_candidates": sum(bool(r["epa_ventilating_fan_pattern_candidates"]) for r in records),
              "skus_without_pattern_candidates": sum(not r["epa_ventilating_fan_pattern_candidates"] for r in records),
              "candidate_unit_type_counts": dict(sorted(type_counts.items())),
              "source_hashes": {"epa_rows_sha256": epa["rows_sha256"]},
              "model_candidate_contract": "Literal equality or positional pattern candidate; '*' consumes one A-Z/0-9 position. Candidate is not a certification match.",
              "assessment_contract": "No hood classification, applicability, certification identity, publication consistency, severity, or compliance rule is applied.",
              "scope": "Hood PDP claims and raw EPA ventilating-fan model-pattern candidates. EPA unit_type and market remain source evidence; no legal or product-type conclusion.",
              "collection_contract": collection["contract"], "records": records}
    dest = Path(output)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "hood-epa-source-candidates.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("## Hood EPA source candidates\n\n")
            stream.write(f"PDP exact SKUs: **{len(records)}**; EPA Samsung rows: **{len(epa_rows)}**; model-pattern candidate rows: **{candidate_rows}**. No compliance decisions were run.\n\n")
            stream.write("| Exact SKU | PLP flag | PDP logo count | PDP Specs claim count | EPA pattern rows | EPA unit types |\n|---|---|---:|---:|---:|---|\n")
            for row in records:
                claim = row["energy_star_claim_sources_raw"]
                candidates = row["epa_ventilating_fan_pattern_candidates"]
                types = sorted({str(x.get("unit_type_raw") or "(blank)") for x in candidates})
                values = [row["exact_sku"], claim.get("plp_energy_star_flag_raw"), len(claim.get("rendered_attributed_badges_raw", [])), len(claim.get("pdp_visible_spec_energy_star_rows_raw", [])), len(candidates), ", ".join(types)]
                stream.write("| " + " | ".join(str(v if v is not None else "(not observed)").replace("|", "\\|") for v in values) + " |\n")
            stream.write("\nEPA patterns are candidate evidence only. Product subtype, applicability, and all audit outcomes remain NOT_EVALUATED.\n")
    print(json.dumps({"status": report["status"], "population_count": len(records), "epa_samsung_rows": len(epa_rows),
                      "pattern_candidate_rows": candidate_rows, "candidate_unit_type_counts": report["candidate_unit_type_counts"],
                      "applicability": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"}, sort_keys=True), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--collection-run-id", required=True)
    parser.add_argument("--epa-root", required=True)
    parser.add_argument("--epa-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build(args.collection_root, args.collection_run_id, args.epa_root, args.epa_run_id, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


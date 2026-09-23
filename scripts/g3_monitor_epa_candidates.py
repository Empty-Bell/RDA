"""Join exact-SKU monitor PDP claims to raw EPA display model candidates."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

from epa_only_rules import model_pattern_candidate

COLLECTION_CONTRACT = "G3_MONITOR_EXACT_SKU_PDP_V1"
EPA_CONTRACT = "G3_MONITOR_EPA_CURRENT_SOURCE_V1"
REPORT_CONTRACT = "G3_MONITOR_EPA_SOURCE_CANDIDATES_V1"
DATASET = "qbg3-d468"


def read_json(path):
    return json.loads(Path(path).read_bytes())


def load_collection(root, run_id):
    root = Path(root)
    summary = read_json(root / "collection-summary.json")
    if (summary.get("status") != "PASS" or summary.get("contract") != COLLECTION_CONTRACT
            or str(summary.get("collection_run_id")) != str(run_id)):
        raise ValueError("Monitor PDP collection is not the requested successful contract/run")
    products = read_json(root / "products.json")
    expected = summary.get("coverage", {}).get("population_count")
    paths = sorted(root.glob("pdp/*/result.json"))
    if not isinstance(expected, int) or len(products) != expected or len(paths) != expected:
        raise ValueError("Monitor PDP collection is incomplete")
    skus = [row.get("exact_sku") for row in products]
    if len(set(skus)) != expected:
        raise ValueError("Monitor population has duplicate exact SKUs")
    claims, facts = {}, {}
    for path in paths:
        row = read_json(path)
        sku = row.get("exact_sku")
        if sku not in set(skus) or row.get("status") != "VERIFIED_EXACT_IDENTITY":
            raise ValueError("Monitor PDP result is failed, duplicate, or outside population")
        claim = row.get("energy_star_claim_sources_raw")
        if not isinstance(claim, dict) or claim.get("exact_sku") != sku:
            raise ValueError("Monitor claim evidence lacks exact-SKU provenance")
        snapshot_raw = path.with_name("snapshot.json").read_bytes()
        if hashlib.sha256(snapshot_raw).hexdigest() != row.get("snapshot_sha256"):
            raise ValueError("Monitor PDP snapshot hash mismatch")
        snapshot = json.loads(snapshot_raw)
        if snapshot.get("target_sku") != sku or sku in claims:
            raise ValueError("Monitor snapshot identity is invalid or duplicated")
        claims[sku] = {**claim,
                       "pdp_logo_inspection_raw": snapshot.get("primary_logo_inspection"),
                       "pdp_spec_surface_inspection_raw": snapshot.get("spec_surface_inspection"),
                       "pdp_visible_spec_energy_star_rows_raw": snapshot.get("visible_spec_energy_star_rows", [])}
        facts[sku] = row.get("pdp_facts_raw", {})
    if set(claims) != set(skus):
        raise ValueError("Monitor PDP result set differs from population")
    return products, claims, facts, summary


def load_epa(root, run_id):
    root = Path(root)
    summary = read_json(root / "capture-summary.json")
    raw = (root / "samsung-current-rows.json").read_bytes()
    if (summary.get("status") != "PASS" or summary.get("contract") != EPA_CONTRACT
            or summary.get("dataset_id") != DATASET or str(summary.get("capture_run_id")) != str(run_id)
            or hashlib.sha256(raw).hexdigest() != summary.get("rows_sha256")):
        raise ValueError("Monitor EPA capture identity/hash is invalid")
    rows = json.loads(raw)
    if not isinstance(rows, list) or len(rows) != summary.get("row_count"):
        raise ValueError("Monitor EPA rows do not match capture summary")
    if any(not isinstance(row, dict) or not row.get("source_row_id") or not row.get("pd_id")
           or not row.get("model_number") for row in rows):
        raise ValueError("EPA row lacks source/model identity")
    return rows, summary


def project_candidate(row, candidate):
    keep = ("source_row_id", "pd_id", "brand_name", "model_number", "model_name", "additional_model_information", "display_type",
            "markets", "date_certified", "screen_size_inches", "on_mode_power_watts", "sleep_mode_power_watts",
            "off_mode_power_watts", "monitor_total_energy", "maximum_total_energy", "maximum_power_delivery_w")
    return {f"{key}_raw": row.get(key) for key in keep} | {
        "candidate_source_field": candidate["candidate_source_field"],
        "model_pattern_candidate": candidate["candidate"],
    }


def additional_model_patterns(value):
    """Return only standalone model-like tokens explicitly listed by EPA."""
    if not isinstance(value, str):
        return []
    patterns = []
    for token in re.split(r"[;,]", value):
        token = token.strip()
        if (len(token) >= 4 and re.fullmatch(r"[A-Z0-9*./-]+", token, re.I)
                and re.search(r"[A-Z0-9]", token, re.I) and token not in patterns):
            patterns.append(token)
    return patterns


def build(collection_root, collection_run_id, epa_root, epa_run_id, output):
    products, claims, facts, collection = load_collection(collection_root, collection_run_id)
    epa_rows, epa = load_epa(epa_root, epa_run_id)
    records, type_counts = [], Counter()
    all_epa_type_counts = Counter(str(row.get("display_type") or "(blank)") for row in epa_rows)
    for product in sorted(products, key=lambda row: row["exact_sku"]):
        sku = product["exact_sku"]
        candidates, leading_l_diagnostics = [], []
        for source in epa_rows:
            declared_patterns = [("model_number", source.get("model_number"))]
            declared_patterns.extend(("additional_model_information", pattern)
                                     for pattern in additional_model_patterns(source.get("additional_model_information")))
            seen = set()
            source_matches_sku = False
            for source_field, pattern in declared_patterns:
                matched = model_pattern_candidate(pattern, sku)
                if matched is None:
                    continue
                source_matches_sku = True
                signature = (source_field, pattern)
                if signature in seen:
                    continue
                seen.add(signature)
                item = project_candidate(source, {"candidate_source_field": source_field,
                                                  "candidate": matched})
                candidates.append(item)
                type_counts[str(source.get("display_type") or "(blank)")] += 1
            if sku.startswith("L") and not source_matches_sku:
                for source_field, pattern in declared_patterns:
                    matched_without_l = model_pattern_candidate(pattern, sku[1:])
                    if matched_without_l is not None:
                        leading_l_diagnostics.append({
                            "source_row_id_raw": source.get("source_row_id"),
                            "pd_id_raw": source.get("pd_id"),
                            "candidate_source_field": source_field,
                            "model_pattern_raw": pattern,
                            "epa_model_number_raw": source.get("model_number"),
                            "epa_additional_model_information_raw": source.get("additional_model_information"),
                            "display_type_raw": source.get("display_type"),
                            "markets_raw": source.get("markets"),
                            "diagnostic_only_match_after_dropping_initial_L": matched_without_l,
                        })
        records.append({"exact_sku": sku, "pdp_product_facts_raw": facts.get(sku, {}),
                        "energy_star_claim_sources_raw": claims[sku],
                        "epa_display_pattern_candidates": candidates,
                        "epa_leading_l_only_diagnostics": leading_l_diagnostics,
                        "applicability": "NOT_EVALUATED", "certification_identity": "NOT_EVALUATED",
                        "publication_consistency": "NOT_EVALUATED", "assessment": "NOT_EVALUATED"})
    candidate_rows = sum(len(row["epa_display_pattern_candidates"]) for row in records)
    report = {"contract": REPORT_CONTRACT, "status": "SOURCE_CANDIDATES_READY", "source_validation": "PASS",
              "collection_run_id": str(collection_run_id), "epa_capture_run_id": str(epa_run_id),
              "git_sha": os.getenv("GITHUB_SHA"), "captured_at": datetime.now(timezone.utc).isoformat(),
              "population_count": len(records), "epa_samsung_row_count": len(epa_rows),
              "epa_model_pattern_candidate_row_count": candidate_rows,
              "skus_with_pattern_candidates": sum(bool(r["epa_display_pattern_candidates"]) for r in records),
              "skus_without_pattern_candidates": sum(not r["epa_display_pattern_candidates"] for r in records),
              "skus_with_leading_l_only_diagnostics": sum(bool(r["epa_leading_l_only_diagnostics"]) for r in records),
              "leading_l_only_diagnostic_row_count": sum(len(r["epa_leading_l_only_diagnostics"]) for r in records),
              "candidate_display_type_counts": dict(sorted(type_counts.items())),
              "all_epa_display_type_counts": dict(sorted(all_epa_type_counts.items())),
              "source_hashes": {"epa_rows_sha256": epa["rows_sha256"]},
              "model_candidate_contract": "Literal equality or positional pattern candidate from either EPA model_number or a standalone model-like token in EPA additional_model_information; '*' consumes one A-Z/0-9 position. Candidate is not a certification match.",
              "assessment_contract": "No monitor classification, applicability, certification identity, publication consistency, severity, or compliance rule is applied.",
              "scope": "Monitor PDP claims and raw EPA display model-pattern candidates. EPA display_type and market remain source evidence; no legal or product-type conclusion.",
              "collection_contract": collection["contract"], "records": records}
    dest = Path(output)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "monitor-epa-source-candidates.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("## Monitor EPA source candidates\n\n")
            stream.write(f"PDP exact SKUs: **{len(records)}**; EPA Samsung rows: **{len(epa_rows)}**; model-pattern candidate rows: **{candidate_rows}**. No compliance decisions were run.\n\n")
            stream.write("| Exact SKU | PLP flag | PDP logo count | PDP Specs claim count | EPA pattern rows | EPA unit types |\n|---|---|---:|---:|---:|---|\n")
            for row in records:
                claim = row["energy_star_claim_sources_raw"]
                candidates = row["epa_display_pattern_candidates"]
                types = sorted({str(x.get("display_type_raw") or "(blank)") for x in candidates})
                values = [row["exact_sku"], claim.get("plp_energy_star_flag_raw"), len(claim.get("rendered_attributed_badges_raw", [])), len(claim.get("pdp_visible_spec_energy_star_rows_raw", [])), len(candidates), ", ".join(types)]
                stream.write("| " + " | ".join(str(v if v is not None else "(not observed)").replace("|", "\\|") for v in values) + " |\n")
            stream.write("\nEPA patterns are candidate evidence only. Product subtype, applicability, and all audit outcomes remain NOT_EVALUATED.\n")
    print(json.dumps({"status": report["status"], "population_count": len(records), "epa_samsung_rows": len(epa_rows),
                      "pattern_candidate_rows": candidate_rows, "candidate_display_type_counts": report["candidate_display_type_counts"],
                      "all_epa_display_type_counts": report["all_epa_display_type_counts"],
                      "leading_l_only_diagnostic_sku_count": report["skus_with_leading_l_only_diagnostics"],
                      "leading_l_only_diagnostic_examples": [{"sku": row["exact_sku"],
                          "patterns": [{"source_field": x["candidate_source_field"],
                                        "pattern": x["model_pattern_raw"],
                                        "epa_model_number": x["epa_model_number_raw"],
                                        "display_type": x["display_type_raw"],
                                        "markets": x["markets_raw"], "pd_id": x["pd_id_raw"]}
                                       for x in row["epa_leading_l_only_diagnostics"]]}
                          for row in records if row["epa_leading_l_only_diagnostics"]][:30],
                      "epa_model_samples": [{"model_number": row.get("model_number"), "model_name": row.get("model_name"),
                          "additional_model_information": row.get("additional_model_information"),
                          "display_type": row.get("display_type"), "markets": row.get("markets"), "pd_id": row.get("pd_id")}
                          for row in sorted(epa_rows, key=lambda item: (str(item.get("display_type") or ""), str(item.get("model_number") or "")))[:40]],
                      "publication_by_sku": [{"sku": row["exact_sku"],
                          "plp_energy_star_flag_raw": row["energy_star_claim_sources_raw"].get("plp_energy_star_flag_raw"),
                          "pdp_logo_count": len(row["energy_star_claim_sources_raw"].get("rendered_attributed_badges_raw", [])),
                          "pdp_spec_claim_count": len(row["energy_star_claim_sources_raw"].get("pdp_visible_spec_energy_star_rows_raw", [])),
                          "epa_candidates": len(row["epa_display_pattern_candidates"]),
                          "epa_candidate_types": sorted({str(c.get("display_type_raw") or "(blank)") for c in row["epa_display_pattern_candidates"]})}
                          for row in records],
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


"""Assess the rendered US Tablet PLP population against complete EPA Current rows."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

from epa_only_rules import us_market_state


MODEL = re.compile(r"SM-[A-Z0-9]+\Z")
MODEL_TOKEN = re.compile(r"(?<![A-Z0-9])SM-[A-Z0-9]+(?![A-Z0-9])")
TRUE = {"y", "yes", "true", "1"}
FALSE = {"n", "no", "false", "0"}
OUT_OF_STOCK_PDP_INSPECTION = "PDP_NOT_REACHABLE_FROM_PLP_WHILE_STOCK_FLAG_N"
OUT_OF_STOCK_ROUTE_OBSERVATION = {
    "basis": "PLP_STOCK_FLAG_N_REQUESTED_PDP_URL_RESOLVES_TO_ANOTHER_EXACT_MODEL",
    "finding": "NONE",
    "note": "The PLP card offers no PDP route while stockFlag is N; the redirect is preserved as evidence only."}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def flag(raw):
    value = str(raw).strip().lower() if raw is not None else ""
    return "PRESENT" if value in TRUE else "ABSENT" if value in FALSE else "UNKNOWN"


def model_tokens(row):
    primary = row.get("model_number")
    tokens = {primary} if isinstance(primary, str) and MODEL.fullmatch(primary) else set()
    additional = row.get("additional_model_information")
    if isinstance(additional, str):
        tokens.update(MODEL_TOKEN.findall(additional))
    return tokens


def publication_points(row):
    claim = row["energy_star_claim_sources_raw"]
    plp = flag(claim.get("plp_energy_star_flag_raw"))
    flags = [flag(value.get("value")) for value in claim.get("pdp_nested_energy_star_fields_raw", [])
             if value.get("name") == "energyStarFlag"]
    if claim.get("rendered_attributed_badges_raw") or "PRESENT" in flags:
        pdp = "PRESENT"
    elif claim.get("pdp_logo_inspection_raw") == "SUPPORTED_PRIMARY_SURFACE_COMPLETE":
        pdp = "ABSENT"
    else:
        pdp = "UNKNOWN"
    specs = row.get("pdp_product_facts_raw", {}).get("spec_fields_raw")
    if not isinstance(specs, list):
        spec = "UNKNOWN"
        selected = []
    else:
        selected = [item for item in specs if isinstance(item, dict)
                    and "energy star" in str(item.get("name", "")).lower()
                    and "certif" in str(item.get("name", "")).lower()]
        values = {flag(item.get("value")) for item in selected}
        spec = "NOT_APPLICABLE" if not selected else next(iter(values)) if len(values) == 1 else "UNKNOWN"
    return {"plp_logo": {"state": plp, "raw_value": claim.get("plp_energy_star_flag_raw")},
            "pdp_logo": {"state": pdp, "raw_flags": flags,
                         "inspection": claim.get("pdp_logo_inspection_raw"),
                         "attributed_badges_raw": claim.get("rendered_attributed_badges_raw", [])},
            "spec_certification": {"state": spec, "field_presence": "PRESENT" if selected else "ABSENT",
                                   "raw_rows": selected}}


def build(candidate_path, epa_root, out):
    candidate = read(candidate_path)
    epa_root = Path(epa_root)
    summary = read(epa_root / "capture-summary.json")
    raw = (epa_root / "samsung-current-rows.json").read_bytes()
    rows = json.loads(raw)
    if (candidate.get("contract") != "G3_TABLET_EPA_SOURCE_CANDIDATES_V1"
            or candidate.get("status") != "SOURCE_CANDIDATES_READY"
            or candidate.get("source_validation") != "PASS"
            or candidate.get("dataset_id") != "rxdj-2c88"
            or summary.get("status") != "PASS" or summary.get("dataset_id") != "rxdj-2c88"
            or str(summary.get("capture_run_id")) != str(candidate.get("epa_capture_run_id"))
            or hashlib.sha256(raw).hexdigest() != summary.get("rows_sha256")
            or len(rows) != summary.get("row_count") or len(rows) != candidate.get("epa_samsung_row_count")):
        raise ValueError("Tablet EPA current source is not complete or bound to candidates")
    source_rows = candidate.get("records", [])
    if (len(source_rows) != candidate.get("population_count")
            or len({row.get("exact_sku") for row in source_rows}) != len(source_rows)):
        raise ValueError("Tablet PLP exact-SKU population is incomplete")
    records, gaps = [], []
    for source in sorted(source_rows, key=lambda row: row["exact_sku"]):
        sku = source["exact_sku"]
        claim = source.get("energy_star_claim_sources_raw") or {}
        redirect = source.get("pdp_identity_failure")
        out_of_stock_route = isinstance(redirect, dict) and redirect.get("plp_stock_flag_raw") == "N"
        if isinstance(redirect, dict):
            if claim.get("exact_sku") != sku or not redirect.get("requested_url") or not redirect.get("final_url"):
                raise ValueError("Tablet PDP redirect finding lacks exact-SKU provenance or source URLs")
        if isinstance(redirect, dict) and not out_of_stock_route:
            # A repeated wrong-model PDP of an in-stock (or stock-unknown) SKU is evidence about the link,
            # not about this SKU's registration or logos: nothing from the redirected model is borrowed.
            plp_raw = claim.get("plp_energy_star_flag_raw")
            records.append({"exact_sku": sku, "grade": "MEDIUM",
                "findings": [{"control": "PDP_IDENTITY", "severity": "MEDIUM",
                              "issue_code": "PDP_LINK_WRONG_MODEL"}],
                "pdp_model_raw": sku, "plp_model_raw": None,
                "pdp_identity_failure": redirect,
                "epa_current_registration": "NOT_EVALUATED", "epa_current_matches_raw": [],
                "publication_points": {
                    "plp_logo": {"state": flag(plp_raw), "raw_value": plp_raw},
                    "pdp_logo": {"state": "UNKNOWN", "inspection": "WRONG_MODEL_PDP"},
                    "spec_certification": {"state": "UNKNOWN", "inspection": "WRONG_MODEL_PDP"}},
                "overall_product_compliance": "NOT_EVALUATED"})
            continue
        model = claim.get("listing_title_raw")
        if claim.get("exact_sku") != sku or not isinstance(model, str) or not MODEL.fullmatch(model):
            gaps.append({"exact_sku": sku, "reason": "EXPLICIT_PLP_MODEL_IDENTITY_UNAVAILABLE"})
            model = None
        matches = [row for row in rows if model and model in model_tokens(row)
                   and str(row.get("type", "")).strip().casefold() == "slate/tablet"
                   and us_market_state(row.get("markets")) == "US"]
        if out_of_stock_route:
            # stockFlag N: the PLP card offers no route to the PDP (Notify me), so the requested PDP
            # URL is recorded as an observation only and the PLP-level controls are assessed.
            plp_raw = claim.get("plp_energy_star_flag_raw")
            not_reachable = {"state": "NOT_APPLICABLE", "inspection": OUT_OF_STOCK_PDP_INSPECTION}
            points = {"plp_logo": {"state": flag(plp_raw), "raw_value": plp_raw},
                      "pdp_logo": dict(not_reachable), "spec_certification": dict(not_reachable)}
        else:
            points = publication_points(source)
        states = [value["state"] for value in points.values() if value["state"] != "NOT_APPLICABLE"]
        registration = "PRESENT" if matches else "ABSENT"
        findings = []
        if registration == "PRESENT" and "ABSENT" in states:
            findings.append({"control": "ENERGY_STAR_PUBLICATION", "severity": "LOW",
                             "issue_code": "SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT"})
        elif registration == "ABSENT" and "PRESENT" in states:
            findings.append({"control": "ENERGY_STAR_PUBLICATION", "severity": "HIGH",
                             "issue_code": "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE"})
        elif "UNKNOWN" in states or not states:
            gaps.append({"exact_sku": sku, "reason": "PUBLICATION_POINT_UNRESOLVED"})
        grade = "HIGH" if any(row["severity"] == "HIGH" for row in findings) else "LOW" if findings else "PASS"
        records.append({"exact_sku": sku, "grade": grade, "findings": findings,
                        "pdp_model_raw": sku, "plp_model_raw": model,
                        **({"pdp_identity_failure": redirect, "pdp_route_observation": OUT_OF_STOCK_ROUTE_OBSERVATION}
                           if out_of_stock_route else {}),
                        "epa_current_registration": registration,
                        "epa_current_matches_raw": matches,
                        "publication_points": points,
                        "overall_product_compliance": "NOT_EVALUATED"})
    counts = Counter(row["grade"] for row in records)
    result = {"contract": "G3_TABLET_FINAL_ASSESSMENT_V1",
              "status": "BLOCKED" if gaps else "PASS", "readiness_gaps": gaps,
              "assessment_run_id": os.getenv("GITHUB_RUN_ID"),
              "candidate_run_id": candidate.get("epa_capture_run_id"),
              "collection_run_id": candidate.get("collection_run_id"),
              "captured_at": datetime.now(timezone.utc).isoformat(),
              "sku_count": len(records),
              "counts": {level: counts.get(level, 0) for level in ("PASS", "HIGH", "MEDIUM", "LOW")},
              "records": records, "overall_product_compliance": "NOT_EVALUATED"}
    destination = Path(out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "assessment.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result["counts"], "readiness_gaps": gaps}, ensure_ascii=False), flush=True)
    return 1 if gaps else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("candidates", "epa-root", "out"):
        parser.add_argument("--" + option, required=True)
    args = parser.parse_args()
    raise SystemExit(build(args.candidates, args.epa_root, args.out))

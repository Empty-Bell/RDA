"""Grade approved TV identity, label availability, and ENERGY STAR publication controls."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path


CONTRACT = "G3_TV_ASSESSMENT_V1"
TRUE = {"y", "yes", "true", "1"}
FALSE = {"n", "no", "false", "0"}
RANK = {"PASS": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def flag(value):
    normalized = str(value).strip().lower() if value is not None else ""
    return "PRESENT" if normalized in TRUE else "ABSENT" if normalized in FALSE else "UNKNOWN"


def points(result):
    claim = result.get("energy_star_claim_sources_raw") or {}
    plp = flag(claim.get("plp_energy_star_flag_raw"))
    flags = [flag(row.get("value")) for row in claim.get("pdp_nested_energy_star_fields_raw", [])
             if row.get("name") == "energyStarFlag"]
    if claim.get("rendered_attributed_badges_raw") or "PRESENT" in flags:
        pdp = "PRESENT"
    elif flags and set(flags) == {"ABSENT"} and claim.get("pdp_logo_inspection_raw") == "SUPPORTED_PRIMARY_SURFACE_COMPLETE":
        pdp = "ABSENT"
    else:
        pdp = "UNKNOWN"
    spec_fields = (result.get("pdp_facts_raw") or {}).get("spec_fields_raw")
    if not isinstance(spec_fields, list):
        spec = "UNKNOWN"
        selected = []
    else:
        selected = [row for row in spec_fields if isinstance(row, dict)
                    and "energy star" in str(row.get("name", "")).lower()
                    and "certif" in str(row.get("name", "")).lower()]
        values = {flag(row.get("value")) for row in selected}
        spec = ("NOT_APPLICABLE" if not selected else
                next(iter(values)) if len(values) == 1 else "UNKNOWN")
    return {"plp_logo": {"state": plp, "raw_value": claim.get("plp_energy_star_flag_raw")},
            "pdp_logo": {"state": pdp, "raw_flags": flags,
                         "inspection": claim.get("pdp_logo_inspection_raw")},
            "spec_certification": {"state": spec, "raw_rows": selected,
                                   "field_presence": "PRESENT" if selected else "ABSENT"}}


def assess(comparison_path, collection_root, out):
    comparison = read(comparison_path)
    if comparison.get("status") != "PASS" or comparison.get("contract") != "G3_TV_MODEL_IDENTITY_CANDIDATES_V1":
        raise ValueError("TV comparison is not a successful supported artifact")
    root = Path(collection_root)
    collection = read(root / "collection-summary.json")
    if collection.get("status") != "PASS" or str(collection.get("collection_run_id")) != str(comparison.get("collection_run_id")):
        raise ValueError("TV collection and comparison source run IDs differ")
    results = [read(path) for path in root.glob("pdp/*/result.json")]
    by_sku = {row.get("exact_sku"): row for row in results}
    rows = comparison.get("rows", [])
    if (len(rows) != comparison.get("population_count") or len(by_sku) != len(results)
            or set(by_sku) != {row.get("exact_sku") for row in rows}):
        raise ValueError("TV assessment source populations differ")

    records, gaps = [], []
    for source in sorted(rows, key=lambda item: item["exact_sku"]):
        sku = source["exact_sku"]
        result = by_sku[sku]
        model = source.get("model_comparison") or {}
        if result.get("status") != "VERIFIED_EXACT_IDENTITY" or model.get("pdp") != "EXACT_SKU_IDENTITY_VERIFIED":
            gaps.append({"exact_sku": sku, "reason": "PDP_IDENTITY_UNVERIFIED"})
        label_state = model.get("label")
        findings = []
        if label_state == "LABEL_NOT_ACCESSIBLE":
            if not source.get("finding_candidates"):
                gaps.append({"exact_sku": sku, "reason": "UNREADABLE_LABEL_WITHOUT_SOURCE_FINDING"})
            else:
                findings.append({"control": "ENERGYGUIDE_READABILITY", "severity": "HIGH",
                                 "issue_code": "ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE"})
        elif label_state == "NO_LABEL_DOCUMENT":
            documents = (result.get("pdp_facts_raw") or {}).get("energyguide_documents")
            if documents != []:
                gaps.append({"exact_sku": sku, "reason": "LABEL_DOCUMENT_STATE_UNRESOLVED"})
            else:
                findings.append({"control": "ENERGYGUIDE_DOCUMENT", "severity": "HIGH",
                                 "issue_code": "ENERGYGUIDE_DOCUMENT_MISSING_CANDIDATE"})
        elif label_state != "MODEL_PATTERN_MATCHED" or not source.get("label_prefix_matches"):
            gaps.append({"exact_sku": sku, "reason": "LABEL_MODEL_IDENTITY_UNRESOLVED"})

        publication = points(result)
        states = [point["state"] for point in publication.values()]
        epa_state = model.get("epa_current")
        if epa_state == "CURRENT_US_MODEL_MATCHED" and source.get("epa_us_match_count", 0) > 0:
            registration = "PRESENT"
            if "ABSENT" in states:
                findings.append({"control": "ENERGY_STAR_PUBLICATION", "severity": "LOW",
                                 "issue_code": "SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT"})
            elif "UNKNOWN" in states:
                gaps.append({"exact_sku": sku, "reason": "PUBLICATION_POINT_UNRESOLVED"})
        elif epa_state == "NO_CURRENT_MODEL_MATCH" and not source.get("epa_current_model_matches"):
            registration = "ABSENT"
            if "PRESENT" in states:
                findings.append({"control": "ENERGY_STAR_PUBLICATION", "severity": "HIGH",
                                 "issue_code": "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE"})
            elif "UNKNOWN" in states:
                gaps.append({"exact_sku": sku, "reason": "PUBLICATION_POINT_UNRESOLVED"})
        else:
            registration = "UNKNOWN"
            gaps.append({"exact_sku": sku, "reason": "EPA_CURRENT_REGISTRATION_UNRESOLVED"})
        grade = max((item["severity"] for item in findings), key=RANK.__getitem__, default="PASS")
        records.append({"exact_sku": sku, "grade": grade, "findings": findings,
                        "epa_current_registration": registration, "publication_points": publication,
                        "label_model_state": label_state,
                        "label_model_patterns_raw": source.get("label_model_patterns_raw", []),
                        "epa_current_models_raw": [row.get("model_number_raw") for row in source.get("epa_current_model_matches", [])],
                        "label_document_accessibility": source.get("label_document_accessibility"),
                        "pdp_url": result.get("final_url"),
                        "overall_product_compliance": "NOT_EVALUATED"})

    counts = Counter(row["grade"] for row in records)
    report = {"contract": CONTRACT, "status": "BLOCKED" if gaps else "PASS",
              "comparison_run_id": comparison.get("comparison_run_id"),
              "collection_run_id": comparison.get("collection_run_id"),
              "epa_capture_run_id": comparison.get("epa_capture_run_id"),
              "assessment_run_id": os.getenv("GITHUB_RUN_ID"),
              "captured_at": datetime.now(timezone.utc).isoformat(),
              "sku_count": len(records), "counts": {level: counts.get(level, 0) for level in ("PASS", "HIGH", "MEDIUM", "LOW")},
              "readiness_gaps": gaps, "records": records,
              "annual_energy_comparison": "OUT_OF_SCOPE",
              "overall_product_compliance": "NOT_EVALUATED"}
    destination = Path(out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "assessment.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "counts": report["counts"], "readiness_gaps": gaps}, ensure_ascii=False), flush=True)
    return 1 if gaps else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", required=True)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raise SystemExit(assess(args.comparison, args.collection_root, args.out))

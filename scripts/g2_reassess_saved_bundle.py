"""Reapply current approved refrigerator rules to one accepted, frozen G2 source bundle."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import zipfile

from g2_energy_star_assessment import build_assessment
from g2_refrigerator_control_summary import build_summary


RANK = {"PASS": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}


def unique_json(archive, suffix):
    names = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise ValueError(f"Expected one {suffix} in G2 source artifact")
    return json.loads(archive.read(names[0]))


def build(source_zip, out):
    with zipfile.ZipFile(source_zip) as archive:
        report = unique_json(archive, "/report.json")
        review = unique_json(archive, "/three-point-input-review.json")
        original_energy = unique_json(archive, "/energy-star-assessment.json")
        numeric = report.get("energyguide_numeric", {})
        model = report.get("energyguide_model_pattern", {})
    run_id = report.get("run_id")
    population = len(report.get("rows", []))
    if (not run_id or not population or review.get("source_run_id") != run_id
            or original_energy.get("source_run_id") != run_id
            or any(section.get("source_run_id") != run_id for section in (numeric, model))):
        raise ValueError("Frozen G2 control sections do not share one source execution")
    revised_energy = build_assessment(review, expected_exact_skus=population,
                                      query_completeness="COMPLETE_OBSERVED_QUERY")
    projected = dict(report)
    projected["energy_star_publication"] = revised_energy
    summary = build_summary(projected)
    energy_by_sku = {row["exact_sku"]: row for row in revised_energy["records"]}
    numeric_by_sku = {row["exact_sku"]: row for row in numeric["records"]}
    model_by_sku = {row["exact_sku"]: row for row in model["records"]}
    if not (set(energy_by_sku) == set(numeric_by_sku) == set(model_by_sku)
            == {row["exact_sku"] for row in summary["records"]}):
        raise ValueError("Frozen G2 control populations differ")
    records, gaps = [], []
    for source in summary["records"]:
        sku = source["exact_sku"]
        e, n, m = energy_by_sku[sku], numeric_by_sku[sku], model_by_sku[sku]
        if e["outcome"] == "NOT_EVALUATED" or n["display_outcome"] == "NOT_EVALUATED" or m["display_outcome"] == "NOT_EVALUATED":
            gaps.append({"exact_sku": sku, "reason": "CONTROL_NOT_EVALUATED"})
        grade = max((finding["severity"] for finding in source["findings"]),
                    key=RANK.__getitem__, default="PASS")
        records.append({"exact_sku": sku, "grade": grade,
                        "findings": source["findings"], "controls": source["controls"],
                        "energy_star_publication": e, "energyguide_numeric": n,
                        "energyguide_model_pattern": m,
                        "overall_product_compliance": "NOT_EVALUATED"})
    counts = Counter(row["grade"] for row in records)
    result = {"contract": "G2_REFRIGERATOR_SAVED_SOURCE_REASSESSMENT_V1",
              "status": "BLOCKED" if gaps else "PASS", "readiness_gaps": gaps,
              "source_execution_id": run_id, "source_workflow_run_id": os.getenv("SOURCE_RUN_ID"),
              "reassessment_run_id": os.getenv("GITHUB_RUN_ID"),
              "captured_at": datetime.now(timezone.utc).isoformat(),
              "sku_count": population, "counts": {level: counts.get(level, 0) for level in RANK},
              "finding_count": summary["counts"]["finding_count"],
              "affected_sku_count": summary["counts"]["affected_sku_count"],
              "records": records, "overall_product_compliance": "NOT_EVALUATED"}
    destination = Path(out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "reassessment.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "finding_count": result["finding_count"], "readiness_gaps": gaps}, ensure_ascii=False), flush=True)
    return 1 if gaps else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raise SystemExit(build(args.source_zip, args.out))

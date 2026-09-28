"""Reconcile one hosted 11-family acquisition/assessment run without publishing."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


FAMILIES = (
    "refrigerator", "dishwasher", "washer", "tv", "range", "cooktop",
    "dryer", "hood", "monitor", "computer", "tablet",
)
G3 = set(FAMILIES[:4])
GRADES = ("PASS", "HIGH", "MEDIUM", "LOW")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build(root, run_id, output):
    root, output = Path(root), Path(output)
    errors, families, all_skus = [], [], set()
    for family in FAMILIES:
        manifest_path = root / "unified" / family / "unified-family-manifest.json"
        if not manifest_path.is_file():
            errors.append(f"FAMILY_MANIFEST_MISSING:{family}")
            continue
        manifest = read(manifest_path)
        if (manifest.get("contract") != "RDA_UNIFIED_FAMILY_EXECUTION_V1"
                or manifest.get("family") != family or manifest.get("run_id") != run_id):
            errors.append(f"FAMILY_RUN_IDENTITY_DIFFERS:{family}")
            continue
        relative = manifest.get("assessment_path", "")
        if not relative.startswith(f"runtime/unified/{family}/"):
            errors.append(f"ASSESSMENT_PATH_OUTSIDE_FAMILY:{family}")
            continue
        assessment = root / relative.removeprefix("runtime/")
        if not assessment.is_file():
            errors.append(f"ASSESSMENT_MISSING:{family}")
            continue
        digest = hashlib.sha256(assessment.read_bytes()).hexdigest()
        report = read(assessment)
        rows = report.get("records", report.get("rows"))
        if (digest != manifest.get("assessment_sha256") or report.get("status") != "PASS"
                or report.get("readiness_gaps") or not isinstance(rows, list)
                or len(rows) != manifest.get("sku_count") or not rows):
            errors.append(f"ASSESSMENT_INCOMPLETE:{family}")
            continue
        skus = [row.get("exact_sku") for row in rows]
        grades = [row.get("grade", row.get("display_outcome")) for row in rows]
        counts = Counter(grades)
        if (any(not sku for sku in skus) or len(set(skus)) != len(skus)
                or any(grade not in GRADES for grade in grades)
                or any(counts[level] != manifest.get("counts", {}).get(level) for level in GRADES)
                or any((family, sku) in all_skus for sku in skus)):
            errors.append(f"MODEL_GRADE_OR_POPULATION_DIFFERS:{family}")
        all_skus.update((family, sku) for sku in skus)
        if family != "refrigerator":
            recon_families = ("computer", "chromebook") if family == "computer" else (family,)
            for source in recon_families:
                recon_path = root / "source-recon" / source / "recon.json"
                if not recon_path.is_file() or str(read(recon_path).get("run_id")) != run_id:
                    errors.append(f"SOURCE_RECON_IDENTITY_DIFFERS:{source}")
        else:
            checkpoints = list((root / "g2").glob("*/checkpoint.json"))
            if (len(checkpoints) != 1 or read(checkpoints[0]).get("status") != "PASS"
                    or str(read(checkpoints[0]).get("github_run_id")) != run_id):
                errors.append("REFRIGERATOR_SOURCE_CHECKPOINT_MISSING")
        families.append({"family": family, "sku_count": len(rows),
                         "counts": {level: counts[level] for level in GRADES},
                         "assessment_contract": report.get("contract"),
                         "assessment_sha256": digest})
    group = lambda names: {level: sum(row["counts"][level] for row in families
                                      if row["family"] in names) for level in GRADES}
    result = {"contract": "RDA_UNIFIED_FULL_RUN_GATE_V1",
              "run_id": run_id, "captured_at": datetime.now(timezone.utc).isoformat(),
              "execution_status": "PASS" if not errors and len(families) == len(FAMILIES) else "FAIL",
              "single_source_run": not errors and len(families) == len(FAMILIES),
              "family_count": len(families), "model_count": sum(row["sku_count"] for row in families),
              "grade_counts": group(set(FAMILIES)),
              "g3_scope": {"families": 4, "model_count": sum(row["sku_count"] for row in families if row["family"] in G3),
                           "grade_counts": group(G3)},
              "g4_scope": {"families": 7, "model_count": sum(row["sku_count"] for row in families if row["family"] not in G3),
                           "grade_counts": group(set(FAMILIES) - G3)},
              "families": families, "integrity_errors": errors,
              "dashboard_publication": "NOT_EVALUATED",
              "overall_product_compliance": "NOT_EVALUATED"}
    output.mkdir(parents=True, exist_ok=True)
    (output / "unified-report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result["execution_status"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raise SystemExit(build(args.root, args.run_id, args.out))

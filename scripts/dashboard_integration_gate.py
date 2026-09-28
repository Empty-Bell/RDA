"""Bind accepted family artifacts to the mixed Pages snapshot and expose open gates."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import os


GRADES = ("PASS", "HIGH", "MEDIUM", "LOW")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows_by_key(rows, family, key="model"):
    result = {(family, row[key]): row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate {family} model keys")
    return result


def artifact_rows(report):
    rows = report.get("rows") if isinstance(report.get("rows"), list) else report.get("records")
    if not isinstance(rows, list):
        raise ValueError("Assessment has no model rows")
    return rows


def grade(row):
    return row.get("display_outcome", row.get("grade"))


def build(docs, manifest_path, artifacts_root, out):
    docs, artifacts_root, out = map(Path, (docs, artifacts_root, out))
    manifest, snapshot = read(manifest_path), read(docs / "model-data.json")
    if manifest.get("contract") != "RDA_INTEGRATION_MANIFEST_V1":
        raise ValueError("Unsupported integration manifest")
    families = snapshot.get("families", [])
    family_by_name = {row["family"]: row for row in families}
    records = snapshot.get("records", [])
    keys = [(row["family"], row["model"]) for row in records]
    errors = []
    if len(family_by_name) != len(families) or len(set(keys)) != len(keys):
        errors.append("DUPLICATE_FAMILY_OR_MODEL_KEY")
    if any(row.get("grade") not in GRADES for row in records):
        errors.append("UNCLASSIFIED_MODEL")
    if sum(row.get("population", 0) for row in families) != len(records):
        errors.append("FAMILY_POPULATION_SUM_DIFFERS")
    counts = Counter((row["family"], row["grade"]) for row in records)
    for family in families:
        name = family["family"]
        if sum(counts[name, level] for level in GRADES) != family.get("population"):
            errors.append(f"FAMILY_POPULATION_MISMATCH:{name}")
        if any(counts[name, level] != family.get(level.lower()) for level in GRADES):
            errors.append(f"FAMILY_GRADE_COUNT_MISMATCH:{name}")
    record_by_key = dict(zip(keys, records))
    for row in records:
        evidence = row.get("evidence_url", "")
        if not evidence.startswith("./evidence/") or not (docs / evidence[2:]).is_file():
            errors.append(f"EVIDENCE_FILE_MISSING:{row['family']}:{row['model']}")

    csv_keys = {}
    with (docs / "report-data.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            key = (row["family"], row["model"])
            if key in csv_keys:
                errors.append(f"CSV_DUPLICATE_MODEL:{key[0]}:{key[1]}")
            csv_keys[key] = row
    if set(csv_keys) != set(record_by_key):
        errors.append("CSV_MODEL_POPULATION_DIFFERS")
    else:
        for key, row in csv_keys.items():
            if row["grade"] != record_by_key[key]["grade"]:
                errors.append(f"CSV_GRADE_DIFFERS:{key[0]}:{key[1]}")
    field_count = 0
    with (docs / "report-all-fields.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            field_count += 1
            key = (row["family"], row["model"])
            if key not in record_by_key or row["grade"] != record_by_key[key]["grade"]:
                errors.append(f"RAW_EXPORT_MODEL_OR_GRADE_DIFFERS:{key[0]}:{key[1]}")
                break
    if field_count != snapshot.get("field_count"):
        errors.append("RAW_EXPORT_FIELD_COUNT_DIFFERS")
    if not (docs / "report-data.xlsx").is_file():
        errors.append("EXCEL_EXPORT_MISSING")

    accepted = []
    for item in manifest["accepted_family_artifacts"]:
        family = item["family"]
        path = artifacts_root / family / item["report_file"]
        report = read(path)
        source_rows = artifact_rows(report)
        by_sku = {row.get("exact_sku"): row for row in source_rows}
        dashboard_rows = {row["model"]: row for row in records if row["family"] == family}
        if (report.get("status") != "PASS" or report.get("contract") != item["report_contract"]
                or len(by_sku) != len(source_rows) or set(by_sku) != set(dashboard_rows)
                or len(source_rows) != report.get("sku_count")):
            errors.append(f"ACCEPTED_ARTIFACT_SCOPE_DIFFERS:{family}")
        if family_by_name.get(family, {}).get("run_id") != item["run_id"]:
            errors.append(f"ACCEPTED_RUN_NOT_PUBLISHED:{family}")
        for sku, source in by_sku.items():
            dashboard = dashboard_rows.get(sku)
            if dashboard and (dashboard["grade"] != grade(source)
                              or {finding.get("issue_code") for finding in dashboard.get("findings", [])}
                              != {finding.get("issue_code") for finding in source.get("findings", [])}):
                errors.append(f"ACCEPTED_ASSESSMENT_DIFFERS:{family}:{sku}")
        accepted.append({"family": family, "run_id": item["run_id"],
                         "model_count": len(source_rows), "counts": report.get("counts")})

    pending = []
    for item in manifest["accepted_snapshot_pending_refresh"]:
        family = item["family"]
        if family_by_name.get(family, {}).get("run_id") != item["formal_run_id"]:
            pending.append({"family": family, "reason": item["reason"],
                            "published_run_id": family_by_name.get(family, {}).get("run_id"),
                            "formal_run_id": item["formal_run_id"]})
    pending += [{"family": family, "reason": "FAMILY_FORMAL_ACCEPTANCE_PENDING"}
                for family in manifest["family_acceptance_pending"]]
    covered = {item["family"] for item in accepted + pending}
    if covered != set(family_by_name) or len(covered) != len(accepted) + len(pending):
        errors.append("INTEGRATION_MANIFEST_FAMILY_COVERAGE_DIFFERS")
    result = {"contract": "RDA_DASHBOARD_INTEGRATION_GATE_V1",
              "execution_status": "FAIL" if errors else "PASS",
              "formal_readiness": "BLOCKED" if errors or pending else "READY_FOR_FORMAL_REVIEW",
              "integration_run_id": os.getenv("GITHUB_RUN_ID"),
              "captured_at": datetime.now(timezone.utc).isoformat(),
              "dashboard_run_number": snapshot.get("run_number"),
              "model_count": len(records), "family_count": len(families),
              "grade_counts": {level: sum(row["grade"] == level for row in records) for level in GRADES},
              "raw_export_field_count": field_count,
              "accepted_family_artifacts": accepted,
              "pending_family_gates": pending, "integrity_errors": errors,
              "single_source_run": False,
              "overall_product_compliance": "NOT_EVALUATED"}
    out.mkdir(parents=True, exist_ok=True)
    (out / "integration-report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("docs", "manifest", "artifacts-root", "out"):
        parser.add_argument("--" + option, required=True)
    args = parser.parse_args()
    raise SystemExit(build(args.docs, args.manifest, args.artifacts_root, args.out))

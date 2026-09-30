"""Refresh the static Pages snapshot from one hosted dishwasher control chain."""

import argparse
import csv
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


MODEL_IDENTITY_POLICY = (
    "Printed EnergyGuide/PDP model identity accepts a matching fixed prefix "
    "despite trailing-star and remaining-suffix length differences; "
    "EPA Current registration uses separate source matching."
)


def normalized_grade_policy(policy):
    """Keep the dishwasher model-identity policy exactly once across runs."""
    base = policy.replace(MODEL_IDENTITY_POLICY, "").strip()
    return f"{base} {MODEL_IDENTITY_POLICY}".strip()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def flat(value, prefix=""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from flat(child, f"{prefix}.{key}" if prefix else key)
    elif isinstance(value, list):
        if not value:
            yield prefix, "[]"
        else:
            for index, child in enumerate(value):
                yield from flat(child, f"{prefix}[{index}]")
    else:
        yield prefix, "" if value is None else str(value)


def number(value):
    return format(Decimal(value), "f") if value is not None else None


def build(docs, assessment_path, numeric_path, model_path, energy_path, package_path, run_id):
    docs = Path(docs)
    snapshot = read(docs / "model-data.json")
    assessment, numeric, model, energy, package = map(read, (
        assessment_path, numeric_path, model_path, energy_path, package_path))
    if assessment.get("status") != "PASS" or not assessment.get("rows") or assessment.get("sku_count") != len(assessment["rows"]):
        raise ValueError("Hosted dishwasher assessment is incomplete")
    if any(source.get("status") != "PASS" for source in (numeric, model, energy, package)):
        raise ValueError("One hosted source control is incomplete")
    if not (numeric.get("source_bundle_fingerprint") == model.get("source_bundle_fingerprint") == energy.get("source_bundle_fingerprint") == package.get("source_bundle_fingerprint")):
        raise ValueError("Hosted source fingerprints differ")
    if not numeric.get("source_package_sha256") or numeric["source_package_sha256"] != model.get("source_package_sha256"):
        raise ValueError("Numeric and model controls use different comparison packages")
    by_sku = lambda rows: {item["exact_sku"]: item for item in rows}
    a, n, m, e, p = (by_sku(rows) for rows in (assessment["rows"], numeric["rows"], model["records"], energy["records"], package["rows"]))
    if not (set(a) == set(n) == set(m) == set(e) == set(p)):
        raise ValueError("Hosted dishwasher SKU sets differ")
    records = [item for item in snapshot["records"] if item["family"] == "식기세척기"]
    if {item["model"] for item in records} != set(a):
        raise ValueError("Pages dishwasher population differs from hosted assessment")
    if assessment["sku_count"] != len(records) or sum(assessment["counts"].values()) != len(records):
        raise ValueError("Hosted dishwasher counts do not cover the Pages population")
    old_run = snapshot["run_number"]
    old_time = snapshot["built_at"]
    changes = []
    for record in records:
        sku = record["model"]
        outcome = a[sku]["display_outcome"]
        old_grade = record["grade"]
        old_codes = {item["issue_code"] for item in record["findings"]}
        new_codes = {item["issue_code"] for item in a[sku]["findings"]}
        if old_grade != outcome or old_codes != new_codes:
            changes.append({"family": "식기세척기", "model": sku, "previous_grade": old_grade, "grade": outcome})
        record.update(grade=outcome, findings=a[sku]["findings"], run_id=str(run_id),
                      run_url=f"https://github.com/Empty-Bell/RDA/actions/runs/{run_id}",
                      epa_registration=e[sku]["epa_current_registration"]["state"],
                      points={key: value["state"] for key, value in e[sku]["publication_points"].items()})
        summary = record["raw_summary"]
        label_value = n[sku]["energyguide_annual_energy"]
        epa_value = n[sku]["epa_annual_energy"]
        summary.update(label_model=" · ".join(m[sku]["energyguide_model_patterns_visual_reviewed"] or m[sku]["energyguide_model_patterns_raw"]),
                       label_energy=f"{number(label_value['value'])} kWh/year" if label_value["state"] == "VALUE" else None,
                       label_energy_state=label_value["state"],
                       epa_energy=f"{number(epa_value['value'])} kWh/year" if epa_value["state"] == "VALUE" else None,
                       epa_model=" · ".join(m[sku]["epa_current_model_candidates_raw"]) or None,
                       epa_registration=e[sku]["epa_current_registration"]["state"])
        old_detail_path = docs / record["evidence_url"].removeprefix("./")
        detail = read(old_detail_path)
        detail.update(grade=outcome, assessment=a[sku], source_comparison=p[sku],
                      model_comparison=m[sku], numeric_comparison=n[sku],
                      energy_star_assessment=e[sku], source_run=str(run_id))
        from refresh_pages_refrigerator import evidence_name
        detail_path = old_detail_path.with_name(evidence_name(run_id, record["family"], sku))
        record["evidence_url"] = "./evidence/" + detail_path.name
        detail_path.write_text(json.dumps(detail, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    family = next(item for item in snapshot["families"] if item["family"] == "식기세척기")
    family.update({key.lower(): assessment["counts"][key] for key in ("PASS", "HIGH", "MEDIUM", "LOW")})
    family.update(run_id=str(run_id), run_url=f"https://github.com/Empty-Bell/RDA/actions/runs/{run_id}",
                  grade_state="assessed", note=("원본 US EnergyGuide 라벨 21개 모델명 일치. "
                    f"EPA 공식 모델군 확인을 포함한 재판정: PASS {assessment['counts']['PASS']} / "
                    f"HIGH {assessment['counts']['HIGH']} / MEDIUM {assessment['counts']['MEDIUM']} / "
                    f"LOW {assessment['counts']['LOW']}. 호스팅 출처 지문과 판정 게이트 통과."))
    snapshot["run_number"] = old_run + 1
    snapshot["built_at"] = datetime.now(timezone.utc).isoformat()
    snapshot["source_note"] = "Latest reviewed grade evidence by family; dishwasher refreshed from bound hosted G3 controls. Source runs across families are not one unified run."
    snapshot["grade_policy"] = normalized_grade_policy(snapshot["grade_policy"])
    snapshot["run_comparison"] = {"available": True, "current_run": old_run + 1, "previous_run": old_run,
        "previous_built_at": old_time, "source_runs_changed": True,
        "new": [item for item in changes if item["previous_grade"] == "PASS" and item["grade"] != "PASS"],
        "resolved": [item for item in changes if item["previous_grade"] != "PASS" and item["grade"] == "PASS"],
        "recurred": [], "changed": changes, "scope_added": [], "scope_removed": []}
    snapshot_path = docs / "model-data.json"
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    headers = ["family", "model", "grade", "pdp_model", "pdp_title", "pdp_energy", "pdp_capacity", "pdp_logo", "plp_logo", "plp_logo_raw", "spec_certification", "label_model", "label_energy", "label_energy_state", "label_capacity", "epa_registration", "epa_match_status", "epa_model", "epa_energy", "epa_capacity", "findings", "pdp_url", "label_urls"]
    with (docs / "report-data.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream); writer.writerow(headers)
        for record in snapshot["records"]:
            summary = record.get("raw_summary") or {}
            writer.writerow([record["family"], record["model"], record["grade"], *[summary.get(key) for key in headers[3:10]],
                record.get("points", {}).get("spec_certification"), *[summary.get(key) for key in headers[11:20]],
                json.dumps(record["findings"], ensure_ascii=False), record.get("pdp_url"), " | ".join(record.get("label_urls", []))])
    full_path = docs / "report-all-fields.csv"
    temporary = docs / "report-all-fields.tmp.csv"
    field_count = 0
    with full_path.open("r", encoding="utf-8-sig", newline="") as source, temporary.open("w", encoding="utf-8-sig", newline="") as target:
        reader = csv.DictReader(source)
        writer = csv.writer(target); writer.writerow(reader.fieldnames)
        for row in reader:
            if row["family"] != "식기세척기":
                writer.writerow([row[key] for key in reader.fieldnames]); field_count += 1
        for record in records:
            detail = read(docs / record["evidence_url"].removeprefix("./"))
            for source_name, value in detail.items():
                if source_name in {"model", "family", "grade", "source_run"}:
                    continue
                for field_path, field_value in flat(value):
                    writer.writerow(["식기세척기", record["model"], record["grade"], source_name, field_path, field_value]); field_count += 1
    temporary.replace(full_path)
    snapshot["field_count"] = field_count
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"run_number": snapshot["run_number"], "dishwasher_counts": assessment["counts"], "field_count": field_count, "changed": len(changes)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for option in ("docs", "assessment", "numeric", "model", "energy", "package", "run-id"):
        parser.add_argument(f"--{option}", required=True)
    args = parser.parse_args()
    build(args.docs, args.assessment, args.numeric, args.model, args.energy, args.package, args.run_id)

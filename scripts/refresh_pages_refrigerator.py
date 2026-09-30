"""Refresh refrigerator Pages records from the hosted current-rule frozen-source replay."""

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile

from refresh_pages_washer_tv import flat


FAMILY = "냉장고"
FAMILY_SLUG = {"냉장고": "refrigerator", "식기세척기": "dishwasher", "세탁기": "washer",
               "TV": "tv", "레인지": "range", "쿡탑": "cooktop", "의류건조기": "dryer",
               "후드": "hood", "모니터": "monitor", "컴퓨터": "computer", "태블릿": "tablet"}


def evidence_name(run_id, family, sku):
    return f"{run_id}_{FAMILY_SLUG[family]}_{sku.replace('/', '_')}.json"
HEADERS = ["family", "model", "grade", "pdp_model", "pdp_title", "pdp_energy", "pdp_capacity",
           "pdp_logo", "plp_logo", "plp_logo_raw", "spec_certification", "label_model", "label_energy",
           "label_energy_state", "label_capacity", "epa_registration", "epa_match_status", "epa_model",
           "epa_energy", "epa_capacity", "findings", "pdp_url", "label_urls"]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def source_report(path):
    with zipfile.ZipFile(path) as archive:
        reports = [name for name in archive.namelist() if name.endswith("/report.json")]
        numeric = [name for name in archive.namelist() if name.endswith("/projection.json")]
        if len(reports) != 1 or len(numeric) != 1:
            raise ValueError("Accepted G2 artifact has no unique canonical report and EPA numeric projection")
        return json.loads(archive.read(reports[0])), json.loads(archive.read(numeric[0]))


def build(docs, assessment_path, source_zip):
    docs = Path(docs)
    assessment = read(assessment_path)
    source, epa_numeric = source_report(source_zip)
    snapshot = read(docs / "model-data.json")
    if (assessment.get("status") != "PASS" or assessment.get("readiness_gaps")
            or assessment.get("source_execution_id") != source.get("run_id")
            or epa_numeric.get("contract") != "G2_EPA_REFRIGERATOR_NUMERIC_ENRICHMENT_V1"
            or epa_numeric.get("status") != "PASS"
            or epa_numeric.get("source_run_id") != source.get("run_id")
            or assessment.get("sku_count") != len(source.get("rows", []))):
        raise ValueError("Refrigerator reassessment is not bound to complete G2 source")
    a = {row["exact_sku"]: row for row in assessment["records"]}
    s = {row["exact_sku"]: row for row in source["rows"]}
    epa_values = {row["exact_sku"]: row for row in epa_numeric.get("records", [])}
    records = [row for row in snapshot["records"] if row["family"] == FAMILY]
    if (set(a) != set(s) or set(a) != set(epa_values) or set(a) != {row["model"] for row in records}
            or len(a) != assessment["sku_count"] or sum(assessment["counts"].values()) != len(a)):
        raise ValueError("Refrigerator source or Pages population differs")
    old_run, old_time = snapshot["run_number"], snapshot["built_at"]
    changes = []
    run_id = str(assessment["reassessment_run_id"])
    if not run_id or run_id == "None":
        raise ValueError("Hosted reassessment run ID is missing")
    for record in records:
        sku = record["model"]
        current = a[sku]
        grade = current["grade"]
        if grade not in {"PASS", "HIGH", "MEDIUM", "LOW"}:
            raise ValueError(f"Unclassified refrigerator: {sku}")
        if record["grade"] != grade or {x["issue_code"] for x in record["findings"]} != {x["issue_code"] for x in current["findings"]}:
            changes.append({"family": FAMILY, "model": sku, "previous_grade": record["grade"], "grade": grade})
        publication = current["energy_star_publication"]
        points = publication["publication_points"]
        registration = publication["epa_current_index_registration"]
        prior_url = record["evidence_url"]
        prior = read(docs / prior_url.removeprefix("./"))
        record.update(grade=grade, findings=current["findings"], run_id=run_id,
                      run_url=f"https://github.com/Empty-Bell/RDA/actions/runs/{run_id}",
                      epa_registration=registration["state"],
                      points={key: value["state"] for key, value in points.items()})
        raw = record["raw_summary"]
        raw.update(epa_registration=registration["state"], pdp_logo=points["pdp_logo"]["state"],
                   plp_logo=points["plp_logo"]["state"],
                   epa_model=" · ".join(str(row.get("model_number_raw", "")) for row in registration.get("candidates", [])) or None)
        family_rows = [row for row in registration.get("candidates", []) if row.get("source_dataset_id")]
        if family_rows:
            raw["epa_energy"] = (f"{family_rows[0]['annual_energy_use_kwh_yr']} kWh/year"
                                 if family_rows[0].get("annual_energy_use_kwh_yr") is not None else None)
            raw["epa_capacity"] = (f"{family_rows[0]['capacity_total_volume_ft3']} cu.ft."
                                   if family_rows[0].get("capacity_total_volume_ft3") is not None else None)
        for finding in current["energyguide_numeric"].get("findings", []):
            evidence = finding.get("evidence") or {}
            if finding.get("field") == "capacity_cu_ft":
                raw["label_capacity"] = f"{evidence['label_amount']} cu.ft." if evidence.get("label_amount") is not None else None
                raw["epa_capacity"] = f"{evidence['epa_amount']} cu.ft." if evidence.get("epa_amount") is not None else None
            elif finding.get("field") == "annual_energy_kwh":
                raw["label_energy"] = f"{evidence['label_amount']} kWh/year" if evidence.get("label_amount") is not None else None
                raw["epa_energy"] = f"{evidence['epa_amount']} kWh/year" if evidence.get("epa_amount") is not None else None
        detail = {"model": sku, "family": FAMILY, "grade": grade,
                  "assessment": current, "frozen_canonical_source_row": s[sku],
                  "source_epa_numeric": epa_values[sku],
                  "source_epa_family": family_rows,
                  "source_run": run_id, "source_workflow_run_id": assessment["source_workflow_run_id"],
                  "previous_evidence_url": prior_url,
                  "prior_raw_evidence": {key: value for key, value in prior.items()
                                         if key not in {"model", "family", "grade", "assessment", "source_run"}}}
        detail_path = docs / "evidence" / evidence_name(run_id, FAMILY, sku)
        detail_path.write_text(json.dumps(detail, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        record["evidence_url"] = "./evidence/" + detail_path.name

    family = next(row for row in snapshot["families"] if row["family"] == FAMILY)
    family.update({level.lower(): assessment["counts"][level] for level in ("PASS", "HIGH", "MEDIUM", "LOW")})
    family.update(run_id=run_id, run_url=f"https://github.com/Empty-Bell/RDA/actions/runs/{run_id}",
                  grade_state="assessed",
                  note=(f"같은 실행의 EPA 현행 Index와 냉장고·냉동고 공식 제품군 행을 교차 확인: "
                        f"PASS {assessment['counts']['PASS']} / HIGH {assessment['counts']['HIGH']} / "
                        f"MEDIUM {assessment['counts']['MEDIUM']} / LOW {assessment['counts']['LOW']}. "
                        "용량 차이와 PDP 연간 사용량 누락 포함; Specs 필드 부재는 No와 구분."))
    snapshot["run_number"] = old_run + 1
    snapshot["built_at"] = datetime.now(timezone.utc).isoformat()
    snapshot["source_note"] = "Current-rule refrigerator replay and accepted G3 family controls; family source runs differ and are not one unified collection."
    snapshot["run_comparison"] = {"available": True, "current_run": old_run + 1, "previous_run": old_run,
                                  "previous_built_at": old_time, "source_runs_changed": True,
                                  "new": [row for row in changes if row["previous_grade"] == "PASS"],
                                  "resolved": [row for row in changes if row["grade"] == "PASS"],
                                  "recurred": [], "changed": changes, "scope_added": [], "scope_removed": []}

    with (docs / "report-data.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(HEADERS)
        for record in snapshot["records"]:
            raw = record.get("raw_summary") or {}
            writer.writerow([record["family"], record["model"], record["grade"],
                             *[raw.get(key) for key in HEADERS[3:10]], record.get("points", {}).get("spec_certification"),
                             *[raw.get(key) for key in HEADERS[11:20]], json.dumps(record["findings"], ensure_ascii=False),
                             record.get("pdp_url"), " | ".join(record.get("label_urls", []))])
    all_fields = docs / "report-all-fields.csv"
    temporary = docs / "report-all-fields.tmp.csv"
    field_count = 0
    with all_fields.open("r", encoding="utf-8-sig", newline="") as source_csv, temporary.open("w", encoding="utf-8-sig", newline="") as target:
        reader = csv.DictReader(source_csv)
        writer = csv.writer(target)
        writer.writerow(reader.fieldnames)
        for row in reader:
            if row["family"] != FAMILY:
                writer.writerow([row[key] for key in reader.fieldnames])
                field_count += 1
        for record in records:
            detail = read(docs / record["evidence_url"].removeprefix("./"))
            for section, value in detail.items():
                if section in {"model", "family", "grade", "source_run"}:
                    continue
                for path, field in flat(value):
                    writer.writerow([FAMILY, record["model"], record["grade"], section, path, field])
                    field_count += 1
    temporary.replace(all_fields)
    snapshot["field_count"] = field_count
    (docs / "model-data.json").write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    from openpyxl import Workbook
    workbook = Workbook(write_only=True)
    for title, path in (("Models", docs / "report-data.csv"), ("All Fields", all_fields)):
        sheet = workbook.create_sheet(title)
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            for row in csv.reader(stream):
                sheet.append(row)
    workbook.save(docs / "report-data.xlsx")
    print(json.dumps({"run_number": snapshot["run_number"], "refrigerator_counts": assessment["counts"],
                      "changed": len(changes), "field_count": field_count}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", required=True)
    parser.add_argument("--assessment", required=True)
    parser.add_argument("--source-zip", required=True)
    args = parser.parse_args()
    build(args.docs, args.assessment, args.source_zip)

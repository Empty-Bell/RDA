"""Refresh six EPA-focused family snapshots from one hosted current-rule replay."""

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

from refresh_pages_refrigerator import HEADERS
from refresh_pages_washer_tv import flat


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build(docs, manifest_path, assessments_root, sources_root):
    docs, assessments_root, sources_root = map(Path, (docs, assessments_root, sources_root))
    manifest, snapshot = read(manifest_path), read(docs / "model-data.json")
    if manifest.get("contract") != "G3_EPA_FAMILY_REPLAY_MANIFEST_V1":
        raise ValueError("Unsupported EPA family manifest")
    inputs = {}
    for item in manifest["families"]:
        family, slug = item["family"], item["slug"]
        report = read(assessments_root / slug / "assessment.json")
        source = read(sources_root / slug / item["candidate_path"])
        if (report.get("status") != "PASS" or report.get("contract") != "G3_EPA_FAMILY_SAVED_SOURCE_REASSESSMENT_V1"
                or report.get("family") != family or report.get("source_run_id") != item["source_run_id"]
                or source.get("contract") != item["source_contract"]):
            raise ValueError(f"{family} hosted assessment and source provenance differ")
        a = {row["exact_sku"]: row for row in report["records"]}
        s = {row["exact_sku"]: row for row in source.get("records", source.get("rows", []))}
        published = {row["model"] for row in snapshot["records"] if row["family"] == family}
        if (not (set(a) == set(s) == published) or len(a) != report["sku_count"]
                or sum(report["counts"].values()) != len(a)):
            raise ValueError(f"{family} source and Pages populations differ")
        inputs[family] = (report, a, s)
    old_run, old_time = snapshot["run_number"], snapshot["built_at"]
    changes = []
    for record in snapshot["records"]:
        family = record["family"]
        if family not in inputs:
            continue
        report, assessed, source = inputs[family]
        sku = record["model"]
        current, candidate = assessed[sku], source[sku]
        grade = current["grade"]
        if grade not in {"PASS", "HIGH", "MEDIUM", "LOW"}:
            raise ValueError(f"Unclassified {family} model: {sku}")
        if record["grade"] != grade or {x["issue_code"] for x in record["findings"]} != {x["issue_code"] for x in current["findings"]}:
            changes.append({"family": family, "model": sku, "previous_grade": record["grade"], "grade": grade})
        run_id = str(report["assessment_run_id"])
        if not run_id or run_id == "None":
            raise ValueError("Hosted EPA family assessment run ID is missing")
        publication = current["energy_star_publication"]
        points = publication["points"]
        registration = current["epa_current_registration"]["state"]
        prior_url = record["evidence_url"]
        prior = read(docs / prior_url.removeprefix("./"))
        record.update(grade=grade, findings=current["findings"], run_id=run_id,
                      run_url=f"https://github.com/Empty-Bell/RDA/actions/runs/{run_id}",
                      epa_registration=registration,
                      points={key: point["state"] for key, point in points.items()})
        record["raw_summary"].update(epa_registration=registration,
                                     plp_logo=points["plp_logo"]["state"],
                                     pdp_logo=points["pdp_logo"]["state"],
                                     pdp_redirect_final_url=(current.get("pdp_identity_failure") or {}).get("final_url"))
        detail = {"model": sku, "family": family, "grade": grade,
                  "assessment": current, "frozen_source_candidate": candidate,
                  "source_run": run_id, "source_workflow_run_id": report["source_run_id"],
                  "previous_evidence_url": prior_url,
                  "prior_raw_evidence": {key: value for key, value in prior.items()
                                         if key not in {"model", "family", "grade", "assessment", "source_run"}}}
        from refresh_pages_refrigerator import evidence_name
        detail_path = docs / "evidence" / evidence_name(run_id, family, sku)
        detail_path.write_text(json.dumps(detail, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        record["evidence_url"] = "./evidence/" + detail_path.name
    for family, (report, _, _) in inputs.items():
        entry = next(row for row in snapshot["families"] if row["family"] == family)
        entry.update({level.lower(): report["counts"][level] for level in ("PASS", "HIGH", "MEDIUM", "LOW")})
        entry.update(run_id=str(report["assessment_run_id"]),
                     run_url=f"https://github.com/Empty-Bell/RDA/actions/runs/{report['assessment_run_id']}",
                     grade_state="assessed",
                     note="저장된 동일 출처에 승인된 EPA Current·ENERGY STAR 공개 규칙을 재적용. Specs 인증 필드 없음은 NOT_APPLICABLE, 명시적 No와 구분.")
    snapshot["run_number"] = old_run + 1
    snapshot["built_at"] = datetime.now(timezone.utc).isoformat()
    snapshot["source_note"] = "Current-rule source-bound family assessments; family source runs differ and are not one unified collection."
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
            if row["family"] not in inputs:
                writer.writerow([row[key] for key in reader.fieldnames])
                field_count += 1
        for record in snapshot["records"]:
            if record["family"] not in inputs:
                continue
            detail = read(docs / record["evidence_url"].removeprefix("./"))
            for section, value in detail.items():
                if section in {"model", "family", "grade", "source_run"}:
                    continue
                for path, field in flat(value):
                    writer.writerow([record["family"], record["model"], record["grade"], section, path, field])
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
    print(json.dumps({"run_number": snapshot["run_number"], "families": len(inputs),
                      "changed": len(changes), "field_count": field_count}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("docs", "manifest", "assessments-root", "sources-root"):
        parser.add_argument("--" + option, required=True)
    args = parser.parse_args()
    build(args.docs, args.manifest, args.assessments_root, args.sources_root)

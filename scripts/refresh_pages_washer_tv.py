"""Publish source-bound Washer and TV family assessments in the mixed Pages snapshot."""

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path


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


def collection(root):
    root = Path(root)
    summary = read(root / "collection-summary.json")
    rows = [read(path) for path in root.glob("pdp/*/result.json")]
    by_sku = {row["exact_sku"]: row for row in rows}
    if summary.get("status") != "PASS" or len(by_sku) != len(rows):
        raise ValueError("PDP collection is incomplete")
    return summary, by_sku


def build(args):
    docs = Path(args.docs)
    snapshot = read(docs / "model-data.json")
    inputs = {}
    for family, assessor, comparator, root in (
            ("세탁기", args.washer_assessment, args.washer_comparison, args.washer_collection),
            ("TV", args.tv_assessment, args.tv_comparison, args.tv_collection)):
        a, c = read(assessor), read(comparator)
        summary, collected = collection(root)
        if (a.get("status") != "PASS" or c.get("status") != "PASS"
                or str(a.get("comparison_run_id")) != str(c.get("comparison_run_id"))
                or str(c.get("collection_run_id")) != str(summary.get("collection_run_id"))):
            raise ValueError(f"{family} assessment and source run IDs differ")
        assessed = {row["exact_sku"]: row for row in a["records"]}
        compared = {row["exact_sku"]: row for row in c["rows"]}
        published = {row["model"] for row in snapshot["records"] if row["family"] == family}
        if not (set(assessed) == set(compared) == set(collected) == published
                and len(published) == a["sku_count"] == sum(a["counts"].values())
                and not a.get("readiness_gaps")):
            raise ValueError(f"{family} population or readiness differs from Pages")
        inputs[family] = a, assessed, compared, collected

    old_run, old_time = snapshot["run_number"], snapshot["built_at"]
    changes = []
    for record in snapshot["records"]:
        family = record["family"]
        if family not in inputs:
            continue
        report, assessed, compared, collected = inputs[family]
        sku = record["model"]
        assessment, comparison, source = assessed[sku], compared[sku], collected[sku]
        grade = assessment.get("display_outcome") if family == "세탁기" else assessment["grade"]
        if grade not in {"PASS", "HIGH", "MEDIUM", "LOW"}:
            raise ValueError(f"Unclassified {family} SKU: {sku}")
        if record["grade"] != grade or {x["issue_code"] for x in record["findings"]} != {x["issue_code"] for x in assessment["findings"]}:
            changes.append({"family": family, "model": sku, "previous_grade": record["grade"], "grade": grade})
        run_id = str(report["assessment_run_id"])
        record.update(grade=grade, findings=assessment["findings"], run_id=run_id,
                      run_url=f"https://github.com/Empty-Bell/RDA/actions/runs/{run_id}",
                      epa_registration=(assessment["epa_current_registration"]["state"] if family == "세탁기"
                                        else assessment["epa_current_registration"]))
        points = assessment["energy_star_publication"]["points"] if family == "세탁기" else assessment["publication_points"]
        record["points"] = {key: value["state"] for key, value in points.items()}
        raw = record["raw_summary"]
        raw.update(epa_registration=record["epa_registration"],
                   pdp_logo=record["points"]["pdp_logo"], plp_logo=record["points"]["plp_logo"])
        if family == "세탁기":
            raw.update(label_model=" · ".join(comparison.get("label_model_patterns_raw", [])) or None,
                       epa_model=" · ".join(assessment["epa_current_registration"]["matched_models_raw"]) or None)
        else:
            raw.update(label_model=" · ".join(comparison.get("label_model_patterns_raw", [])) or None,
                       epa_model=" · ".join(assessment["epa_current_models_raw"]) or None)
        prior = record["evidence_url"]
        prior_detail = read(docs / prior.removeprefix("./"))
        detail = {"model": sku, "family": family, "grade": grade,
                  "assessment": assessment, "collection": source,
                  "source_comparison": comparison,
                  "source_run": run_id, "previous_evidence_url": prior,
                  "prior_raw_evidence": {key: value for key, value in prior_detail.items()
                                         if key in {"snapshot", "bridge", "energyguide_retrieval"}}}
        detail_path = docs / "evidence" / f"{run_id}_{sku.replace('/', '_')}.json"
        detail_path.write_text(json.dumps(detail, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        record["evidence_url"] = "./evidence/" + detail_path.name

    for family in inputs:
        report = inputs[family][0]
        entry = next(row for row in snapshot["families"] if row["family"] == family)
        entry.update({level.lower(): report["counts"][level] for level in ("PASS", "HIGH", "MEDIUM", "LOW")})
        entry.update(run_id=str(report["assessment_run_id"]),
                     run_url=f"https://github.com/Empty-Bell/RDA/actions/runs/{report['assessment_run_id']}",
                     grade_state="assessed")
        if family == "세탁기":
            entry["note"] = "호스팅 최종 판정: PDP·라벨 모델 37개 일치, PASS 30 / MEDIUM 2 / LOW 5. 인증 필드 없음 7개는 명시적 No와 구분."
        else:
            entry["note"] = "호스팅 최종 판정: 읽을 수 있는 라벨 158개 모델 일치. HIGH 8개는 라벨 판독 불가 5, 문서 없음 2, EPA 미등록·ENERGY STAR 표기 1."
    snapshot["run_number"] = old_run + 1
    snapshot["built_at"] = datetime.now(timezone.utc).isoformat()
    snapshot["source_note"] = "Latest source-bound Washer and TV family controls; source runs across families are not one unified audit execution."
    snapshot["run_comparison"] = {
        "available": True, "current_run": old_run + 1, "previous_run": old_run,
        "previous_built_at": old_time, "source_runs_changed": True,
        "new": [row for row in changes if row["previous_grade"] == "PASS"],
        "resolved": [row for row in changes if row["grade"] == "PASS"],
        "recurred": [], "changed": changes, "scope_added": [], "scope_removed": []}

    headers = ["family", "model", "grade", "pdp_model", "pdp_title", "pdp_energy", "pdp_capacity", "pdp_logo", "plp_logo", "plp_logo_raw", "spec_certification", "label_model", "label_energy", "label_energy_state", "label_capacity", "epa_registration", "epa_match_status", "epa_model", "epa_energy", "epa_capacity", "findings", "pdp_url", "label_urls"]
    with (docs / "report-data.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        for record in snapshot["records"]:
            raw = record.get("raw_summary") or {}
            writer.writerow([record["family"], record["model"], record["grade"],
                             *[raw.get(key) for key in headers[3:10]], record.get("points", {}).get("spec_certification"),
                             *[raw.get(key) for key in headers[11:20]],
                             json.dumps(record["findings"], ensure_ascii=False), record.get("pdp_url"),
                             " | ".join(record.get("label_urls", []))])
    all_fields = docs / "report-all-fields.csv"
    temporary = docs / "report-all-fields.tmp.csv"
    field_count = 0
    with all_fields.open("r", encoding="utf-8-sig", newline="") as source, temporary.open("w", encoding="utf-8-sig", newline="") as target:
        reader = csv.DictReader(source)
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
            for source_name, value in detail.items():
                if source_name in {"model", "family", "grade", "source_run"}:
                    continue
                for path, field in flat(value):
                    writer.writerow([record["family"], record["model"], record["grade"], source_name, path, field])
                    field_count += 1
    temporary.replace(all_fields)
    snapshot["field_count"] = field_count
    (docs / "model-data.json").write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    from openpyxl import Workbook
    workbook = Workbook(write_only=True)
    for name, path in (("Models", docs / "report-data.csv"), ("All Fields", all_fields)):
        sheet = workbook.create_sheet(name)
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            for row in csv.reader(stream):
                sheet.append(row)
    workbook.save(docs / "report-data.xlsx")
    print(json.dumps({"run_number": snapshot["run_number"], "field_count": field_count,
                      "changed": changes, "washer": inputs["세탁기"][0]["counts"],
                      "tv": inputs["TV"][0]["counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("docs", "washer-assessment", "washer-comparison", "washer-collection",
                "tv-assessment", "tv-comparison", "tv-collection"):
        parser.add_argument("--" + key, required=True)
    build(parser.parse_args())

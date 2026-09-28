"""Complete the staged mixed-family Pages build with accepted Tablet PLP controls."""

import argparse
import copy
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

from refresh_pages_refrigerator import HEADERS
from refresh_pages_washer_tv import flat


FAMILY = "태블릿"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build(docs, assessment_path, source_path, collection_root):
    docs = Path(docs)
    assessment, source = read(assessment_path), read(source_path)
    snapshot = read(docs / "model-data.json")
    if (assessment.get("status") != "PASS" or assessment.get("readiness_gaps")
            or assessment.get("contract") != "G3_TABLET_FINAL_ASSESSMENT_V1"
            or source.get("contract") != "G3_TABLET_EPA_SOURCE_CANDIDATES_V1"
            or str(assessment.get("candidate_run_id")) != str(source.get("epa_capture_run_id"))):
        raise ValueError("Tablet assessment is not bound to complete EPA candidates")
    a = {row["exact_sku"]: row for row in assessment["records"]}
    s = {row["exact_sku"]: row for row in source["records"]}
    collected = [read(path) for path in Path(collection_root).rglob("pdp/*/result.json")]
    c = {row["exact_sku"]: row for row in collected}
    records = [row for row in snapshot["records"] if row["family"] == FAMILY]
    old_by_sku = {row["model"]: row for row in records}
    added, removed = set(a) - set(old_by_sku), set(old_by_sku) - set(a)
    if (set(a) != set(s) or not set(a) <= set(c) or len(c) != len(collected)
            or len(added) != len(removed) or len(a) != assessment["sku_count"]
            or sum(assessment["counts"].values()) != len(a)):
        raise ValueError("Tablet source or Pages population differs")
    if any(c[sku].get("status") != "VERIFIED_EXACT_IDENTITY" for sku in a):
        raise ValueError("Tablet PLP SKU lacks exact PDP identity")
    for sku in removed:
        snapshot["records"].remove(old_by_sku[sku])
    for sku in sorted(added):
        template = copy.deepcopy(old_by_sku[sorted(removed)[0]])
        template["model"] = sku
        template["evidence_url"] = None
        snapshot["records"].append(template)
    records = [row for row in snapshot["records"] if row["family"] == FAMILY]
    run_id = str(assessment["assessment_run_id"])
    if not run_id or run_id == "None":
        raise ValueError("Hosted Tablet assessment run ID is missing")
    changes = []
    for record in records:
        sku = record["model"]
        current, candidate, collection = a[sku], s[sku], c[sku]
        grade = current["grade"]
        if grade not in {"PASS", "HIGH", "MEDIUM", "LOW"}:
            raise ValueError(f"Unclassified Tablet model: {sku}")
        if record["grade"] != grade or {x["issue_code"] for x in record["findings"]} != {x["issue_code"] for x in current["findings"]}:
            changes.append({"family": FAMILY, "model": sku, "previous_grade": record["grade"], "grade": grade})
        points = current["publication_points"]
        prior_url = record["evidence_url"]
        prior = read(docs / prior_url.removeprefix("./")) if prior_url else {}
        while prior.get("source_run") == run_id:
            nested = prior.get("prior_raw_evidence") or {}
            if "source_candidate" in nested and "previous_evidence_url" in nested:
                prior_url = nested.get("previous_evidence_url")
                prior = nested.get("prior_raw_evidence") or {}
            else:
                prior_url = prior.get("previous_evidence_url")
                prior = nested
        record.update(grade=grade, findings=current["findings"], run_id=run_id,
                      run_url=f"https://github.com/Empty-Bell/RDA/actions/runs/{run_id}",
                      epa_registration=current["epa_current_registration"],
                      points={key: value["state"] for key, value in points.items()},
                      pdp_url=collection.get("final_url"),
                      model_name=current["plp_model_raw"],
                      collection_status=collection.get("status"),
                      spec_rows=len(candidate.get("pdp_product_facts_raw", {}).get("spec_fields_raw", [])),
                      label_count=0, label_urls=[])
        capacity_rows = candidate.get("pdp_product_facts_raw", {}).get("battery_capacity_mah_raw", [])
        record["raw_summary"].update(epa_registration=current["epa_current_registration"],
                                     pdp_logo=points["pdp_logo"]["state"],
                                     pdp_logo_badges=points["pdp_logo"].get("attributed_badges_raw", []),
                                     plp_logo=points["plp_logo"]["state"],
                                     plp_logo_raw=candidate["energy_star_claim_sources_raw"].get("plp_energy_star_flag_raw"),
                                     pdp_model=sku, pdp_title=current["plp_model_raw"],
                                     pdp_capacity=" · ".join(f"{row.get('name')}: {row.get('value')}" for row in capacity_rows) or None,
                                     epa_model=" · ".join(str(row.get("model_number", "")) for row in current["epa_current_matches_raw"]) or None)
        detail = {"model": sku, "family": FAMILY, "grade": grade,
                  "assessment": current, "source_candidate": candidate, "collection": collection,
                  "source_run": run_id, "source_workflow_run_id": source.get("epa_capture_run_id"),
                  "previous_evidence_url": prior_url,
                  "prior_raw_evidence": {key: value for key, value in prior.items()
                                         if key not in {"model", "family", "grade", "assessment", "source_run"}}}
        from refresh_pages_refrigerator import evidence_name
        detail_path = docs / "evidence" / evidence_name(run_id, FAMILY, sku)
        detail_path.write_text(json.dumps(detail, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        record["evidence_url"] = "./evidence/" + detail_path.name
    family = next(row for row in snapshot["families"] if row["family"] == FAMILY)
    family.update({level.lower(): assessment["counts"][level] for level in ("PASS", "HIGH", "MEDIUM", "LOW")})
    family.update(run_id=run_id, run_url=f"https://github.com/Empty-Bell/RDA/actions/runs/{run_id}",
                  collection_run_id=str(assessment["collection_run_id"]),
                  collection_run_url=f"https://github.com/Empty-Bell/RDA/actions/runs/{assessment['collection_run_id']}",
                  grade_state="assessed",
                  note="렌더링된 US PLP 11개 전부 최종 판정. EPA Current 모델명·추가 모델 토큰의 정확 일치와 PLP/PDP 로고를 대조; 11 PASS.")
    snapshot["built_at"] = datetime.now(timezone.utc).isoformat()
    snapshot["source_note"] = "All 11 families have source-bound accepted control artifacts; collection source runs differ and are not one unified audit source run."
    comparison = snapshot.get("run_comparison") or {}
    comparison.setdefault("changed", []).extend(changes)
    comparison.setdefault("new", []).extend(row for row in changes if row["previous_grade"] == "PASS")
    comparison.setdefault("resolved", []).extend(row for row in changes if row["grade"] == "PASS")
    comparison.setdefault("scope_added", []).extend({"family": FAMILY, "model": sku} for sku in sorted(added))
    comparison.setdefault("scope_removed", []).extend({"family": FAMILY, "model": sku} for sku in sorted(removed))
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
    print(json.dumps({"run_number": snapshot["run_number"], "tablet_counts": assessment["counts"],
                      "changed": len(changes), "field_count": field_count}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("docs", "assessment", "source", "collection-root"):
        parser.add_argument("--" + option, required=True)
    args = parser.parse_args()
    build(args.docs, args.assessment, args.source, args.collection_root)

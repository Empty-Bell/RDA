"""Build one reviewable Pages snapshot from one accepted unified source run.

This is a source-bound build step. It writes to a separate output directory;
the published docs tree is never changed until its integration gate passes.
"""

import argparse
import copy
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

from dashboard_integration_gate import build as integration_gate
from g3_epa_family_reassessment import build as reassess_epa
from refresh_pages_refrigerator import build as refresh_refrigerator
from refresh_pages_dishwasher import build as refresh_dishwasher
from refresh_pages_washer_tv import build as refresh_washer_tv
from refresh_pages_washer_tv import flat
from refresh_pages_epa_families import build as refresh_epa
from refresh_pages_tablet import build as refresh_tablet
from audit_history import advance as advance_history, model_transitions, rule_fingerprint
from report_projection import HEADERS as REPORT_HEADERS, korean_description, projection as report_projection


SLUGS = {
    "냉장고": "refrigerator", "식기세척기": "dishwasher", "세탁기": "washer",
    "TV": "tv", "레인지": "range", "쿡탑": "cooktop", "의류건조기": "dryer",
    "후드": "hood", "모니터": "monitor", "컴퓨터": "computer", "태블릿": "tablet",
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reconcile_plp_population(docs, source, gate):
    """Stage the current source population before the family refreshers run."""
    snapshot_path = docs / "model-data.json"
    snapshot = read(snapshot_path)
    run_id = str(gate["run_id"])
    totals = {}
    for family, slug in SLUGS.items():
        manifest = read(source / slug / "unified-family-manifest.json")
        if manifest.get("family") != slug or str(manifest.get("run_id")) != run_id:
            raise ValueError(f"{family} scope source does not match the unified run")
        relative = str(manifest.get("assessment_path") or "")
        prefix = f"runtime/unified/{slug}/"
        if not relative.startswith(prefix):
            raise ValueError(f"{family} assessment path is outside its source artifact")
        report = read(source / slug / relative.removeprefix(prefix))
        rows = report.get("records", report.get("rows"))
        if not isinstance(rows, list) or len(rows) != manifest.get("sku_count"):
            raise ValueError(f"{family} assessment population is incomplete")
        desired = {row["exact_sku"] for row in rows}
        if len(desired) != len(rows):
            raise ValueError(f"{family} assessment has duplicate exact models")
        previous = {row["model"]: row for row in snapshot["records"] if row["family"] == family}
        if len(previous) >= 20 and len(desired) < len(previous) * 0.75:
            raise ValueError(
                f"{family} source population dropped from {len(previous)} to {len(desired)}; "
                "review PLP group options before publishing")
        removed = set(previous) - desired
        added = desired - set(previous)
        if not previous and added:
            raise ValueError(f"{family} has no dashboard record template")
        for record in list(snapshot["records"]):
            if record["family"] == family and record["model"] in removed:
                snapshot["records"].remove(record)
        source_results = {}
        for path in (source / slug).rglob("result.json"):
            result = read(path)
            sku = result.get("exact_sku")
            if sku in desired:
                url = result.get("final_url") or result.get("requested_url")
                if isinstance(url, str) and url.startswith("https://www.samsung.com/us/"):
                    source_results[sku] = result
        for sku in sorted(added):
            if sku not in source_results:
                raise ValueError(f"{family} new PLP model has no verified PDP URL: {sku}")
            result = source_results[sku]
            facts = result.get("pdp_facts_raw") or {}
            claims = result.get("energy_star_claim_sources_raw") or {}
            label_urls = [item["url"] for item in facts.get("energyguide_documents", [])
                          if isinstance(item, dict) and isinstance(item.get("url"), str)]
            record = copy.deepcopy(next(iter(previous.values())))
            record.update(model=sku, grade="PASS", findings=[],
                          pdp_url=result.get("final_url") or result["requested_url"],
                          label_urls=label_urls, epa_registration=None, points={},
                          run_id=None, run_url=None,
                          model_name=claims.get("listing_title_raw"), annual_energy=None,
                          collection_status=result.get("status"),
                          spec_rows=len(facts.get("spec_fields_raw") or []),
                          label_count=len(label_urls))
            record.pop("report", None)
            record.pop("report_description_ko", None)
            record["raw_summary"] = {key: None for key in record["raw_summary"]}
            energy_rows = (facts.get("energy_consumption_raw") or []) + (facts.get("power_consumption_raw") or [])
            capacity_rows = facts.get("capacity_raw") or []
            render_rows = lambda rows: " · ".join(f"{item.get('name')}: {item.get('value')}" for item in rows
                                                if isinstance(item, dict) and item.get("value")) or None
            headings = claims.get("pdp_headings_raw") or []
            record["raw_summary"].update(
                pdp_model=sku, pdp_title=headings[0] if headings else None,
                pdp_energy=render_rows(energy_rows), pdp_capacity=render_rows(capacity_rows),
                plp_logo_raw=claims.get("plp_energy_star_flag_raw"),
                pdp_logo_badges=claims.get("rendered_attributed_badges_raw") or [],
                label_urls=label_urls)
            seed_name = f"scope-seed_{slug}_{sku.replace('/', '_')}.json"
            seed_path = docs / "evidence" / seed_name
            write(seed_path, {"model": sku, "family": family, "scope_added": True})
            record["evidence_url"] = "./evidence/" + seed_name
            snapshot["records"].append(record)
        for record in snapshot["records"]:
            if record["family"] == family and record["model"] in source_results:
                result = source_results[record["model"]]
                record["pdp_url"] = result.get("final_url") or result["requested_url"]
        next(entry for entry in snapshot["families"] if entry["family"] == family)["population"] = len(desired)
        totals[family] = len(desired)
    if len(snapshot["records"]) != gate["model_count"] or sum(totals.values()) != gate["model_count"]:
        raise ValueError("Staged PLP population does not match the accepted unified source count")
    write(snapshot_path, snapshot)


def build(docs_source, artifact_root, unified_report, out, attempt):
    docs_source, artifact_root, out = map(Path, (docs_source, artifact_root, out))
    gate = read(unified_report)
    run_id = str(gate.get("run_id", ""))
    if (gate.get("contract") != "RDA_UNIFIED_FULL_RUN_GATE_V1" or gate.get("execution_status") != "PASS"
            or gate.get("single_source_run") is not True or gate.get("family_count") != len(SLUGS)):
        raise ValueError("Unified source execution has not passed")
    os.environ["GITHUB_RUN_ID"] = run_id
    if out.exists():
        raise ValueError("Output directory must be new to preserve the previous build")
    docs = out / "docs"
    shutil.copytree(docs_source, docs)
    before = read(docs / "model-data.json")
    source = artifact_root / "unified"
    reconcile_plp_population(docs, source, gate)
    g2 = source / "refrigerator"
    refresh_refrigerator(docs, g2 / "assessment/reassessment.json", g2 / "g2-control-source.zip")
    dishwasher = source / "dishwasher"
    refresh_dishwasher(
        docs, dishwasher / "assessment/assessment.json",
        dishwasher / "numeric/numeric-comparison.json",
        dishwasher / "model/model-comparison.json",
        dishwasher / "energy-star/energy-star-assessment.json",
        dishwasher / "package/comparison-package.json", run_id,
    )
    refresh_washer_tv(SimpleNamespace(
        docs=str(docs),
        washer_assessment=str(source / "washer/assessment/assessment.json"),
        washer_comparison=str(source / "washer/comparison/source-comparison-candidates.json"),
        washer_collection=str(source / "washer/collection"),
        tv_assessment=str(source / "tv/assessment/assessment.json"),
        tv_comparison=str(source / "tv/comparison/source-comparison-candidates.json"),
        tv_collection=str(source / "tv/combined"),
    ))
    epa_manifest = read(docs_source / "g3-epa-family-replay-manifest.json")
    for item in epa_manifest["families"]:
        item["source_run_id"] = run_id
    manifest_path = out / "unified-epa-manifest.json"
    write(manifest_path, epa_manifest)
    epa_assessments = out / "epa-reassessment"
    reassess_epa(manifest_path, source, epa_assessments)
    refresh_epa(docs, manifest_path, epa_assessments, source)
    tablet = source / "tablet"
    refresh_tablet(docs, tablet / "assessment/assessment.json",
                   tablet / "epa-candidates/candidates/tablet-epa-source-candidates.json",
                   tablet / "collection")

    after = read(docs / "model-data.json")
    # Earlier snapshots remain available by URL. Re-embedding their full raw
    # payload in every new evidence file would multiply export size each run.
    field_count = 0
    with (docs / "report-all-fields.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["family", "model", "grade", "source", "field_path", "value"])
        for record in after["records"]:
            detail_path = docs / record["evidence_url"].removeprefix("./")
            detail = read(detail_path)
            if str(detail.get("source_run")) != run_id:
                raise ValueError(f"Stale model evidence in unified build: {record['family']} {record['model']}")
            detail.pop("prior_raw_evidence", None)
            detail_path.write_text(json.dumps(detail, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
            for section, value in detail.items():
                if section in {"model", "family", "grade", "source_run"}:
                    continue
                for path, field in flat(value):
                    writer.writerow([record["family"], record["model"], record["grade"], section, path, field])
                    field_count += 1
    after["field_count"] = field_count
    report_rows = []
    for position, record in enumerate(after["records"], 1):
        detail = read(docs / record["evidence_url"].removeprefix("./"))
        row = report_projection(record, detail, position)
        record["report"] = row
        record["report_description_ko"] = korean_description(row["Description"])
        report_rows.append(row)
    with (docs / "report-data.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=REPORT_HEADERS)
        writer.writeheader()
        writer.writerows(report_rows)
    from openpyxl import Workbook
    workbook = Workbook(write_only=True)
    for title, path in (("Models", docs / "report-data.csv"),
                        ("All Fields", docs / "report-all-fields.csv")):
        sheet = workbook.create_sheet(title)
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            for row in csv.reader(stream):
                sheet.append(row)
    workbook.save(docs / "report-data.xlsx")
    prior = {(row["family"], row["model"]): row for row in before["records"]}
    current = {(row["family"], row["model"]): row for row in after["records"]}
    if len(current) != len(after["records"]):
        raise ValueError("Unified dashboard has duplicate exact models")
    changed = []
    for key in sorted(prior.keys() & current.keys()):
        old, row = prior[key], current[key]
        old_issues = {item["issue_code"] for item in old.get("findings", [])}
        new_issues = {item["issue_code"] for item in row.get("findings", [])}
        if old["grade"] != row["grade"] or old_issues != new_issues:
            item = {"family": key[0], "model": key[1],
                    "previous_grade": old["grade"], "grade": row["grade"]}
            changed.append(item)
    after["run_number"] = before["run_number"] + 1
    after["built_at"] = datetime.now(timezone.utc).isoformat()
    after["source_note"] = (
        f"All 11 families were freshly collected and assessed from unified GitHub Actions run {run_id}. "
        "Each exact SKU has one PASS/HIGH/MEDIUM/LOW control grade; whole-product legal compliance is not evaluated."
    )
    history, finding_transitions = advance_history(
        read(docs_source / "history.json"), after, run_id,
        rule_fingerprint(Path(__file__).resolve().parents[1]))
    write(docs / "history.json", history)
    lifecycle = model_transitions(finding_transitions, before, after)
    after["run_comparison"] = {
        "available": True, "current_run": after["run_number"],
        "previous_run": before["run_number"], "previous_built_at": before["built_at"],
        "source_runs_changed": True, "new": lifecycle["new"],
        "resolved": lifecycle["resolved"], "recurred": lifecycle["recurred"],
        "pending_confirmation": lifecycle["pending_confirmation"],
        "changed": changed,
        "scope_added": [{"family": f, "model": m} for f, m in sorted(current.keys() - prior.keys())],
        "scope_removed": [{"family": f, "model": m} for f, m in sorted(prior.keys() - current.keys())],
    }
    for family in after["families"]:
        family["note"] = f"통합 실행 {run_id}의 현재 원본과 승인된 판정 규칙을 적용했습니다."
    (docs / "model-data.json").write_text(
        json.dumps(after, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    accepted = []
    for family, slug in SLUGS.items():
        if family in {"냉장고", "식기세척기", "세탁기", "TV", "태블릿"}:
            filename = "reassessment.json" if family == "냉장고" else "assessment.json"
        else:
            filename = "energy-star-assessment.json"
        report_file = f"unified/{slug}/assessment/{filename}"
        report = read(artifact_root / report_file)
        accepted.append({"family": family, "run_id": run_id,
                         "workflow_path": ".github/workflows/unified-full-audit.yml",
                         "artifact_prefix": f"unified-family-{run_id}-{attempt}-{slug}",
                         "report_file": report_file,
                         "report_contract": report["contract"]})
    manifest = {"contract": "RDA_INTEGRATION_MANIFEST_V1",
                "unified_source_run_id": run_id,
                "accepted_family_artifacts": accepted,
                "accepted_snapshot_pending_refresh": [],
                "family_acceptance_pending": []}
    write(docs / "integration-manifest.json", manifest)
    local_artifacts = out / "integration-input"
    for item in accepted:
        path = local_artifacts / item["family"] / item["report_file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact_root / item["report_file"], path)
    result_code = integration_gate(docs, docs / "integration-manifest.json",
                                   local_artifacts, out / "integration-gate", unified_report)
    if result_code:
        raise ValueError("Unified Pages snapshot differs from source assessments")
    report = read(out / "integration-gate/integration-report.json")
    if (len(report["accepted_family_artifacts"]) != len(SLUGS)
            or report["formal_readiness"] != "READY_FOR_FORMAL_REVIEW"
            or report["single_source_run"] is not True):
        raise ValueError("Unified Pages snapshot lacks a family artifact")
    print(json.dumps({"status": "PASS", "run_id": run_id,
                      "dashboard_run_number": after["run_number"],
                      "model_count": len(after["records"]),
                      "changed": len(changed)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("docs", "artifacts-root", "unified-report", "out", "attempt"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    build(args.docs, args.artifacts_root, args.unified_report, args.out, args.attempt)

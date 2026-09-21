"""Build a deterministic fixture dashboard from one validated refrigerator run."""

import csv
import json
from pathlib import Path
from typing import Any


CONTRACT = "G2_REFRIGERATOR_FIXTURE_DASHBOARD_V1"
ISSUE_META = {
    "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE": ("ENERGY STAR eligibility claim", "Review the Samsung claim against the Current Model Index."),
    "SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT": ("ENERGY STAR publication consistency", "Review the missing Samsung publication point."),
    "PDP_ANNUAL_ENERGY_MISSING": ("PDP annual energy missing", "Add the annual energy value to the PDP specification."),
    "PDP_ENERGYGUIDE_CAPACITY_MISMATCH": ("PDP and EnergyGuide capacity differ", "Align the PDP capacity with the EnergyGuide value."),
}


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build(bundle: dict[str, Any], report: dict[str, Any], output: str | Path) -> dict[str, Any]:
    """Write a single-run dashboard package; no audit semantic is recomputed here."""
    run = bundle.get("manifest", {})
    run_id = run.get("run_id")
    summary = report.get("refrigerator_control_summary", {})
    if report.get("run_id") != run_id or summary.get("source_run_id") != run_id:
        raise ValueError("Dashboard inputs belong to different executions")
    if summary.get("contract") != "G2_REFRIGERATOR_CONTROL_SUMMARY_V1":
        raise ValueError("Refrigerator control summary is invalid")
    report_rows = report.get("rows", [])
    records = {record.get("exact_sku"): record for record in summary.get("records", [])}
    if len(records) != len(summary.get("records", [])) or set(records) != {row.get("exact_sku") for row in report_rows}:
        raise ValueError("Dashboard report SKU coverage is invalid")
    findings, data_rows, compact_evidence = [], [], {}
    for row in sorted(report_rows, key=lambda item: item["exact_sku"]):
        sku = row["exact_sku"]
        control = row.get("refrigerator_control_summary")
        if not isinstance(control, dict) or control != {key: records[sku][key] for key in ("controls", "findings")}:
            raise ValueError("Dashboard control summary does not replay report row")
        controls = control["controls"]
        data_rows.append({"run_id": run_id, "exact_sku": sku,
                          "energy_star_publication": controls["energy_star_publication"]["outcome"],
                          "energyguide_numeric": controls["energyguide_numeric"]["outcome"],
                          "energyguide_model_pattern": controls["energyguide_model_pattern"]["outcome"],
                          "finding_count": len(control["findings"])})
        if control["findings"]:
            compact_evidence[sku] = {"run_id": run_id, "family": "refrigerator", "exact_sku": sku,
                                     "controls": controls, "findings": control["findings"]}
        for finding in control["findings"]:
            title, action = ISSUE_META.get(finding["issue_code"], (finding["issue_code"], "Review the source evidence."))
            evidence_url = f"evidence/{run_id}/refrigerator/{sku}/finding.json"
            findings.append({"run_id": run_id, "finding_id": f"{sku}:{finding['control']}:{finding['issue_code']}",
                             "exact_sku": sku, "control": finding["control"], "severity": finding["severity"],
                             "issue_code": finding["issue_code"], "title": title, "action": action,
                             "public_evidence_url": evidence_url})
    findings.sort(key=lambda item: (item["severity"], item["exact_sku"], item["issue_code"]))
    expected_counts = {"finding_count": len(findings), "affected_sku_count": len({x["exact_sku"] for x in findings}),
                       "findings_by_severity": {level: sum(x["severity"] == level for x in findings) for level in ("HIGH", "MEDIUM", "LOW")}}
    if summary.get("counts") != expected_counts:
        raise ValueError("Dashboard finding counts do not replay control summary")
    dashboard_summary = {"run_id": run_id, "models_in_scope": len(data_rows), "models_evaluated": len(data_rows),
                         **expected_counts, "pipeline_error_count": 0, "compliance_gate": "NOT_EVALUATED",
                         "automatic_final_legal_conclusion": False}
    destination = Path(output)
    data = destination / "data"
    data.mkdir(parents=True, exist_ok=True)
    _write_json(data / "run.json", {key: run.get(key) for key in ("run_id", "git_sha", "started_at", "completed_at", "rule_version", "source_contract_version", "runner")})
    _write_json(data / "summary.json", dashboard_summary)
    _write_json(data / "findings.json", findings)
    _write_json(data / "report_data.json", data_rows)
    _write_json(data / "methodology.json", {"run_id": run_id, "scope": "Refrigerator fixture dashboard", "compliance_gate": "NOT_EVALUATED", "automatic_final_legal_conclusion": False})
    for sku, evidence in compact_evidence.items():
        evidence_path = destination / "evidence" / run_id / "refrigerator" / sku / "finding.json"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(evidence_path, evidence)
    _csv(destination / "findings.csv", findings, ["run_id", "finding_id", "exact_sku", "control", "severity", "issue_code", "title", "action", "public_evidence_url"])
    _csv(destination / "report_data.csv", data_rows, ["run_id", "exact_sku", "energy_star_publication", "energyguide_numeric", "energyguide_model_pattern", "finding_count"])
    (destination / "index.html").write_text("""<!doctype html><meta charset=utf-8><title>Samsung Regulatory Audit</title><main><h1>Samsung Regulatory Audit</h1><p id=run></p><p id=summary></p><label>SKU search <input id=query></label><label>Severity <select id=severity><option value=''>All</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></label><label>Control <select id=control><option value=''>All</option><option>ENERGY_STAR_PUBLICATION</option><option>ENERGYGUIDE_NUMERIC</option></select></label><h2>Findings</h2><table><thead><tr><th>SKU</th><th>Severity</th><th>Control</th><th>Finding</th><th>Evidence</th></tr></thead><tbody id=findings></tbody></table><h2>SKU control outcomes</h2><table><thead><tr><th>SKU</th><th>ENERGY STAR publication</th><th>EnergyGuide numeric</th><th>EnergyGuide model pattern</th><th>Findings</th></tr></thead><tbody id=outcomes></tbody></table></main><script>Promise.all(['data/run.json','data/summary.json','data/findings.json','data/report_data.json'].map(x=>fetch(x).then(x=>x.json()))).then(([r,s,f,d])=>{run.textContent='Run '+r.run_id;summary.textContent=`${s.finding_count} findings across ${s.affected_sku_count} SKUs`;let matches=x=>!query.value||x.exact_sku.includes(query.value.toUpperCase());let draw=()=>{findings.innerHTML=f.filter(x=>matches(x)&&(!severity.value||x.severity==severity.value)&&(!control.value||x.control==control.value)).map(x=>`<tr><td>${x.exact_sku}</td><td>${x.severity}</td><td>${x.control}</td><td>${x.title}</td><td><a href="${x.public_evidence_url}">JSON</a></td></tr>`).join('');outcomes.innerHTML=d.filter(matches).map(x=>`<tr><td>${x.exact_sku}</td><td>${x.energy_star_publication}</td><td>${x.energyguide_numeric}</td><td>${x.energyguide_model_pattern}</td><td>${x.finding_count}</td></tr>`).join('')};severity.onchange=draw;control.onchange=draw;query.oninput=draw;draw()})</script>""", encoding="utf-8")
    return {"contract": CONTRACT, "run_id": run_id, "summary": dashboard_summary,
            "files": sorted(path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file())}

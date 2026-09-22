"""Build a static, filterable dishwasher dashboard from one canonical report."""
import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

SEVERITIES = ("HIGH", "MEDIUM", "LOW", "PASS")


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def build(report_path, out):
    report = json.loads(Path(report_path).read_bytes())
    if report.get("contract") != "G3_DISHWASHER_CANONICAL_REPORT_V1" or report.get("status") != "PASS":
        raise ValueError("Invalid canonical dishwasher report")
    rows, findings = [], []
    for record in report["rows"]:
        energy = record["controls"]["energyguide_numeric"]["comparisons"]
        model = record["controls"]["energyguide_model"]["comparisons"]
        record_findings = record["findings"]
        rows.append({
            "product_group": "Dishwashers", "exact_sku": record["exact_sku"],
            "final_outcome": record["display_outcome"],
            "energy_star_publication": record["controls"]["energy_star_publication"]["outcome"],
            "pdp_vs_energyguide_energy": energy["pdp_vs_energyguide_energy"],
            "energyguide_vs_epa_energy": energy["energyguide_vs_epa_energy"],
            "pdp_vs_energyguide_model": model["pdp_vs_energyguide_model"],
            "pdp_vs_epa_model": model["pdp_vs_epa_model"],
            "energyguide_vs_epa_model": model["energyguide_vs_epa_model"],
            "finding_count": len(record_findings),
            "issue_codes": [finding["issue_code"] for finding in record_findings],
        })
        findings.extend({"product_group": "Dishwashers", "exact_sku": record["exact_sku"], **finding}
                        for finding in record_findings)
    if len(rows) != report["sku_count"]:
        raise ValueError("Dashboard coverage differs from canonical report")
    if len(findings) != report["finding_count"]:
        raise ValueError("Dashboard findings differ from canonical report")
    row_skus = {row["exact_sku"] for row in rows}
    if not all(finding["exact_sku"] in row_skus for finding in findings):
        raise ValueError("Dashboard finding references an unknown SKU")
    verdicts = {severity: sum(row["final_outcome"] == severity for row in rows) for severity in SEVERITIES}
    summary = {
        "models_in_scope": len(rows), "verdicts": verdicts,
        "finding_count": len(findings), "affected_sku_count": len({finding["exact_sku"] for finding in findings}),
        "findings_by_severity": {severity: sum(finding["severity"] == severity for finding in findings)
                                 for severity in ("HIGH", "MEDIUM", "LOW")},
        "overall_product_compliance": "NOT_EVALUATED",
    }
    run = {
        "run_id": os.getenv("GITHUB_RUN_ID", "LOCAL"), "git_sha": os.getenv("GITHUB_SHA", "LOCAL"),
        "generated_at": datetime.now(timezone.utc).isoformat(), "runner": "github-hosted",
        "source_contract_version": report["contract"], "overall_product_compliance": "NOT_EVALUATED",
    }
    controls = ("ENERGY_STAR_PUBLICATION", "MODEL_IDENTITY", "EPA_CURRENT", "ANNUAL_ENERGY")
    matrix = [{"control": control, "finding_count": sum(f["control"] == control for f in findings),
               "affected_sku_count": len({f["exact_sku"] for f in findings if f["control"] == control})}
              for control in controls]
    family = [{"product_group": "Dishwashers", "models_in_scope": len(rows), **verdicts, "finding_count": len(findings)}]
    out = Path(out); data = out / "data"; data.mkdir(parents=True, exist_ok=True)
    for name, value in (("run.json", run), ("summary.json", summary), ("family_summary.json", family),
                        ("control_matrix.json", matrix), ("report-data.json", rows), ("findings.json", findings),
                        ("methodology.json", {"scope": "Dishwasher final verdicts and PDP, EnergyGuide, and current EPA comparisons.", "overall_product_compliance": "NOT_EVALUATED"})):
        _write_json(data / name, value)
    with (out / "report-data.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["exact_sku"])
        writer.writeheader(); writer.writerows(rows)
    with (out / "findings.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["product_group", "exact_sku", "control", "severity", "issue_code"])
        writer.writeheader(); writer.writerows(findings)
    (out / "index.html").write_text("""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Samsung Regulatory Audit</title><style>*{box-sizing:border-box}body{margin:0;background:#f5f7fa;color:#172033;font:14px system-ui,sans-serif}main{max-width:1440px;margin:auto;padding:32px}h1{margin:0;font-size:28px}h2{font-size:18px;margin:28px 0 12px}.meta{color:#586174;margin:8px 0 24px}.cards{display:grid;grid-template-columns:repeat(5,minmax(120px,1fr));gap:12px}.card{background:#fff;border:1px solid #dce1e8;border-radius:8px;padding:16px}.card b{display:block;font-size:25px;margin-top:5px}.high{color:#b42318}.medium{color:#9a6700}.low{color:#175cd3}.pass{color:#027a48}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}input,select,button,a.button{border:1px solid #cdd5df;background:#fff;border-radius:6px;padding:8px;color:#172033;text-decoration:none}button.active{background:#172033;color:#fff}table{border-collapse:collapse;width:100%;background:#fff;border:1px solid #dce1e8}th,td{padding:10px;text-align:left;border-bottom:1px solid #eaecf0;vertical-align:top}th{white-space:nowrap;background:#f9fafb}.section{display:none}.section.active{display:block}@media(max-width:720px){main{padding:16px}.cards{grid-template-columns:repeat(2,1fr)}table{font-size:12px;display:block;overflow:auto}}</style><main><h1>Samsung Regulatory Audit</h1><p class=meta id=meta>Loading current validated run…</p><div class=cards id=cards></div><h2>Audit health</h2><p id=health></p><div class=toolbar><button class=active data-view=queue>Action Queue</button><button data-view=report>All SKU Report</button><a class=button href=findings.csv download>Download findings CSV</a><a class=button href=report-data.csv download>Download full report CSV</a></div><section id=queue class="section active"><h2>Action Queue</h2><div class=toolbar><input id=queueSearch placeholder="Search SKU"><select id=severity><option value="">All severities</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select><select id=control><option value="">All controls</option></select></div><table><thead><tr><th>SKU</th><th>Severity</th><th>Control</th><th>Issue</th></tr></thead><tbody id=findings></tbody></table></section><section id=report class=section><h2>All audited SKUs</h2><div class=toolbar><input id=reportSearch placeholder="Search SKU"><select id=verdict><option value="">All verdicts</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option><option>PASS</option></select></div><table><thead><tr><th>SKU</th><th>Verdict</th><th>Energy Star</th><th>PDP / Label energy</th><th>Label / EPA energy</th><th>PDP / Label model</th><th>PDP / EPA model</th><th>Label / EPA model</th><th>Issues</th></tr></thead><tbody id=rows></tbody></table></section></main><script>Promise.all(['data/run.json','data/summary.json','data/control_matrix.json','data/findings.json','data/report-data.json','data/methodology.json'].map(x=>fetch(x).then(r=>r.json()))).then(([run,summary,matrix,findings,data,method])=>{let findingBody=document.querySelector('#findings'),reportBody=document.querySelector('#rows');meta.textContent=`Run ${run.run_id} · ${run.git_sha.slice(0,7)} · ${run.runner}`;health.textContent=`Scope: ${method.scope} Overall product compliance: ${method.overall_product_compliance}.`;cards.innerHTML=[['In scope',summary.models_in_scope,''],['High',summary.verdicts.HIGH,'high'],['Medium',summary.verdicts.MEDIUM,'medium'],['Low',summary.verdicts.LOW,'low'],['Pass',summary.verdicts.PASS,'pass']].map(x=>`<div class=card>${x[0]}<b class=${x[2]}>${x[1]}</b></div>`).join('');control.innerHTML+=matrix.map(x=>`<option value=${x.control}>${x.control} (${x.finding_count})</option>`).join('');let esc=v=>String(v??'').replace(/[&<>]/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[x]));let drawFindings=()=>{let query=queueSearch.value.toUpperCase();findingBody.innerHTML=findings.filter(x=>(!query||x.exact_sku.includes(query))&&(!severity.value||x.severity===severity.value)&&(!control.value||x.control===control.value)).map(x=>`<tr><td>${esc(x.exact_sku)}</td><td class=${x.severity.toLowerCase()}>${esc(x.severity)}</td><td>${esc(x.control)}</td><td>${esc(x.issue_code)}</td></tr>`).join('')||'<tr><td colspan=4>No matching findings.</td></tr>'};let drawRows=()=>{let query=reportSearch.value.toUpperCase();reportBody.innerHTML=data.filter(x=>(!query||x.exact_sku.includes(query))&&(!verdict.value||x.final_outcome===verdict.value)).map(x=>`<tr><td>${esc(x.exact_sku)}</td><td class=${x.final_outcome.toLowerCase()}>${esc(x.final_outcome)}</td><td>${esc(x.energy_star_publication)}</td><td>${esc(x.pdp_vs_energyguide_energy)}</td><td>${esc(x.energyguide_vs_epa_energy)}</td><td>${esc(x.pdp_vs_energyguide_model)}</td><td>${esc(x.pdp_vs_epa_model)}</td><td>${esc(x.energyguide_vs_epa_model)}</td><td>${esc(x.issue_codes.join(', ')||'—')}</td></tr>`).join('')};[queueSearch,severity,control].forEach(x=>x.oninput=x.onchange=drawFindings);[reportSearch,verdict].forEach(x=>x.oninput=x.onchange=drawRows);document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('.section').forEach(x=>x.classList.toggle('active',x.id===b.dataset.view))});drawFindings();drawRows()})</script></html>""", encoding="utf-8")
    print(json.dumps({"status": "PASS", **summary}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--report", required=True); parser.add_argument("--out", required=True)
    args = parser.parse_args(); build(args.report, args.out)

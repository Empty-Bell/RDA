"""Validate that one refrigerator run's report and dashboard replay each other."""

import csv
import argparse
import json
from pathlib import Path
import zipfile
from typing import Any


CONTRACT = "G2_REFRIGERATOR_ACCEPTANCE_V1"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _unique_skus(rows: Any, label: str) -> set[str]:
    if not isinstance(rows, list):
        raise ValueError(f"{label} rows are invalid")
    skus = [row.get("exact_sku") for row in rows if isinstance(row, dict)]
    if len(skus) != len(rows) or any(not isinstance(sku, str) for sku in skus) or len(set(skus)) != len(skus):
        raise ValueError(f"{label} exact SKU coverage is invalid")
    return set(skus)


def validate(bundle: dict[str, Any], report: dict[str, Any], site: str | Path) -> dict[str, Any]:
    """Reject cross-run, coverage, aggregation and compact-evidence drift."""
    run_id = bundle.get("manifest", {}).get("run_id")
    if not isinstance(run_id, str) or report.get("run_id") != run_id:
        raise ValueError("Acceptance inputs belong to different executions")
    if report.get("assessment_enabled") is not False:
        raise ValueError("Acceptance cannot enable product compliance")
    product_skus = _unique_skus(bundle.get("products"), "Bundle product")
    report_skus = _unique_skus(report.get("rows"), "Report")
    if product_skus != report_skus:
        raise ValueError("Bundle and report SKU coverage differs")

    root = Path(site)
    run = _read_json(root / "data/run.json")
    summary = _read_json(root / "data/summary.json")
    findings = _read_json(root / "data/findings.json")
    data_rows = _read_json(root / "data/report_data.json")
    methodology = _read_json(root / "data/methodology.json")
    if any(item.get("run_id") != run_id for item in (run, summary, methodology)):
        raise ValueError("Dashboard data belongs to another execution")
    if methodology.get("automatic_final_legal_conclusion") is not False or summary.get("compliance_gate") != "NOT_EVALUATED":
        raise ValueError("Dashboard cannot assert final compliance")
    data_skus = _unique_skus(data_rows, "Dashboard report data")
    if data_skus != report_skus:
        raise ValueError("Dashboard report SKU coverage differs")
    if not isinstance(findings, list) or any(not isinstance(item, dict) for item in findings):
        raise ValueError("Dashboard findings are invalid")
    if any(item.get("run_id") != run_id or item.get("exact_sku") not in report_skus for item in findings):
        raise ValueError("Dashboard findings have invalid provenance")
    counts = {level: sum(item.get("severity") == level for item in findings) for level in ("HIGH", "MEDIUM", "LOW")}
    expected_summary = {"models_in_scope": len(report_skus), "models_evaluated": len(report_skus),
                        "finding_count": len(findings), "affected_sku_count": len({item["exact_sku"] for item in findings}),
                        "findings_by_severity": counts}
    if any(summary.get(key) != value for key, value in expected_summary.items()):
        raise ValueError("Dashboard summary does not replay findings")
    for finding in findings:
        evidence_url = finding.get("public_evidence_url")
        if not isinstance(evidence_url, str) or evidence_url.startswith(("/", "http:")) or ".." in Path(evidence_url).parts:
            raise ValueError("Dashboard evidence URL is invalid")
        evidence_path = root / evidence_url
        if not evidence_path.is_file():
            raise ValueError("Dashboard evidence file is missing")
        evidence = _read_json(evidence_path)
        if evidence.get("run_id") != run_id or evidence.get("exact_sku") != finding["exact_sku"]:
            raise ValueError("Dashboard evidence belongs to another finding")
        if not any(item.get("control") == finding.get("control") and item.get("issue_code") == finding.get("issue_code") for item in evidence.get("findings", [])):
            raise ValueError("Dashboard evidence does not replay finding")
    with (root / "findings.csv").open(encoding="utf-8", newline="") as stream:
        if len(list(csv.DictReader(stream))) != len(findings):
            raise ValueError("Findings CSV count differs")
    with (root / "report_data.csv").open(encoding="utf-8", newline="") as stream:
        if len(list(csv.DictReader(stream))) != len(data_rows):
            raise ValueError("Report data CSV count differs")
    return {"contract": CONTRACT, "status": "PASS", "run_id": run_id,
            "exact_sku_count": len(report_skus), "finding_count": len(findings)}


def validate_artifact(artifact: str | Path, output_dir: str | Path) -> dict[str, Any]:
    """Extract and validate the completed G2 artifact without rerunning collection."""
    source = Path(artifact)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        for entry in archive.infolist():
            member = Path(entry.filename)
            if member.is_absolute() or ".." in member.parts or (member.parts and ":" in member.parts[0]):
                raise ValueError("G2 artifact contains an unsafe path")
        archive.extractall(destination)
    bundle_paths = sorted(destination.glob("runtime/g2/**/bundle.json"))
    if len(bundle_paths) != 1:
        raise ValueError("G2 artifact must contain exactly one canonical bundle")
    run_root = bundle_paths[0].parent
    bundle = _read_json(bundle_paths[0])
    report = _read_json(run_root / "report.json")
    result = validate(bundle, report, run_root / "site")
    result["artifact_bundle"] = bundle_paths[0].relative_to(destination).as_posix()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", help="G2 Actions artifact ZIP")
    parser.add_argument("--out", required=True, help="Directory for extracted source and acceptance result")
    args = parser.parse_args()
    result = validate_artifact(args.artifact, args.out)
    output_path = Path(args.out) / "acceptance.json"
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

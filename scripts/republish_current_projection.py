"""Repair derived washer report fields from the already accepted source run.

This keeps the run number, grades, raw evidence and history unchanged. It is
for presentation-only corrections when a fresh source run is blocked.
"""

import argparse
import csv
import json
from pathlib import Path

from publication_bundle import create, digest, verify
from report_projection import HEADERS, korean_description, projection


def rebuild(docs):
    docs = Path(docs)
    manifest = json.loads((docs / "publication-manifest.json").read_text(encoding="utf-8"))
    run_id, source_sha = manifest["run_id"], manifest["source_git_sha"]
    for name, expected in manifest["files"].items():
        if name in {"index.html", "app.js", "styles.css", "report-data.csv", "report-data.xlsx"}:
            continue
        if digest(docs / name) != expected:
            raise ValueError(f"Accepted source bundle has changed: {name}")
    model_path = docs / "model-data.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    changes = []
    for position, record in enumerate(model["records"], 1):
        if record["family"] != "세탁기":
            continue
        evidence = docs / record["evidence_url"].removeprefix("./")
        detail = json.loads(evidence.read_text(encoding="utf-8"))
        if str(detail.get("source_run")) != run_id:
            raise ValueError(f"Washer evidence from another source run: {record['model']}")
        comparison = detail["source_comparison"]
        record["annual_energy"] = detail["assessment"]["annual_energy"]
        selected = comparison.get("pdp_energy_selected_values") or []
        record["raw_summary"]["pdp_energy"] = (
            " · ".join(f"{comparison['pdp_energy_selected_field']}: {value} kWh/year"
                       for value in selected) or None
        )
        projected = projection(record, detail, position)
        if projected != record.get("report"):
            changes.append(record["model"])
        record["report"] = projected
        record["report_description_ko"] = korean_description(projected["Description"])
    model_path.write_text(json.dumps(model, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    with (docs / "report-data.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(record["report"] for record in model["records"])
    from openpyxl import Workbook
    workbook = Workbook(write_only=True)
    for title, name in (("Models", "report-data.csv"), ("All Fields", "report-all-fields.csv")):
        sheet = workbook.create_sheet(title)
        with (docs / name).open("r", encoding="utf-8-sig", newline="") as stream:
            for row in csv.reader(stream):
                sheet.append(row)
    workbook.save(docs / "report-data.xlsx")
    create(docs, run_id, source_sha)
    verify(docs, run_id, source_sha)
    return {"run_id": run_id, "changed_washer_report_rows": changes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    print(json.dumps(rebuild(parser.parse_args().docs), ensure_ascii=False))

"""Build a compact human-review queue from dishwasher EnergyGuide observations."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any


CONTRACT = "G3_DISHWASHER_ENERGYGUIDE_REVIEW_QUEUE_V1"


def _json(path: Path) -> Any:
    return json.loads(path.read_bytes())


def build_queue(observation_root: str | Path, observation_run_id: str) -> dict[str, Any]:
    root = Path(observation_root)
    summary = _json(root / "observation-summary.json")
    if summary.get("status") != "PASS" or str(summary.get("observation_run_id")) != str(observation_run_id):
        raise ValueError("Dishwasher observation artifact is not the requested successful run")
    rows = []
    for item in summary.get("observations", []):
        digest = item.get("pdf_sha256")
        path = root / "pdf" / digest / "observation.json"
        if not path.is_file():
            raise ValueError("Observation JSON is missing for a PDF hash")
        observation = _json(path)
        annual = []
        models = []
        capacities = []
        page_rows = []
        for page in observation.get("pages", []):
            fields = page.get("fields_raw") or {}
            annual.extend(fields.get("energy_candidates_raw", []))
            models.extend(fields.get("model_candidates_raw", []))
            capacities.extend(fields.get("capacity_candidates_raw", []))
            page_rows.append({"page": page.get("page"), "text_source": page.get("text_source"),
                              "text_observation": page.get("text_observation"),
                              "text_preview": page.get("text_raw", "")[:500],
                              "annual_layout_candidate_count": sum(len(x.get("proposals_raw", [])) for x in page.get("annual_layout_candidates_raw", []))})
        rows.append({"pdf_sha256": digest, "sku_count": len(observation.get("sku_documents", [])),
                     "skus": sorted({x.get("exact_sku") for x in observation.get("sku_documents", [])}),
                     "source_urls": observation.get("source_urls", []), "page_count": observation.get("page_count"),
                     "us_heading_candidates": observation.get("label_heading_observations", {}).get("us_energyguide_heading_candidates", []),
                     "canada_heading_candidates": observation.get("label_heading_observations", {}).get("canada_energuide_heading_candidates", []),
                     "annual_energy_candidates_raw": annual, "model_candidates_raw": models,
                     "capacity_candidates_raw": capacities, "pages": page_rows,
                     "selection_status": "REVIEW_REQUIRED", "identity_matching": "NOT_EVALUATED"})
    rows.sort(key=lambda row: row["pdf_sha256"])
    return {"contract": CONTRACT, "observation_run_id": str(observation_run_id),
            "created_at": datetime.now(timezone.utc).isoformat(), "status": "PASS",
            "scope": "Human-review queue only; no field selection, model matching, or compliance assessment",
            "queue_count": len(rows), "rows": rows}


def markdown(queue: dict[str, Any]) -> str:
    lines = ["# Dishwasher EnergyGuide review queue", "",
             "Values below are raw candidates from the same-run PDF observation. They are not selected values.", "",
             "| PDF SHA-256 | SKUs | Pages | US heading candidates | Canada heading candidates | Annual candidates | Model candidates |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in queue["rows"]:
        lines.append(f"| `{row['pdf_sha256']}` | {row['sku_count']} | {row['page_count']} | {len(row['us_heading_candidates'])} | {len(row['canada_heading_candidates'])} | {len(row['annual_energy_candidates_raw'])} | {len(row['model_candidates_raw'])} |")
    lines += ["", "Selection status for every row: `REVIEW_REQUIRED`.", "Field selection, identity matching, and compliance remain `NOT_EVALUATED`."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation-root", required=True)
    parser.add_argument("--observation-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    queue = build_queue(args.observation_root, args.observation_run_id)
    destination = Path(args.out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "review-queue.json").write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "review-queue.md").write_text(markdown(queue), encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Dishwasher EnergyGuide review queue\n\n")
            stream.write(f"Unique PDF hashes queued: **{queue['queue_count']}**\n\n")
            stream.write("No values were selected and no compliance assessment was performed.\n")
    print(json.dumps({"status": queue["status"], "queue_count": queue["queue_count"]}, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

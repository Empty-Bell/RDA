"""Replay preserved EnergyGuide candidates against review-bound selection."""

import argparse
import json
from pathlib import Path
from typing import Any

from g2_label_selection import select_annual_energy


def load_annotations(path: Path) -> dict[str, dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("contract") != "MANUAL_VISUAL_REVIEW_BINDING_ONLY":
        raise ValueError("Unexpected review annotation contract")
    annotations: dict[str, dict[str, Any]] = {}
    for annotation in document.get("annotations", []):
        for sku in annotation.get("exact_skus", []):
            if sku in annotations:
                raise ValueError(f"Duplicate review annotation for {sku}")
            annotations[sku] = annotation
    return annotations


def replay(corpus_root: Path, annotation_path: Path) -> dict[str, Any]:
    annotations = load_annotations(annotation_path)
    records: list[dict[str, Any]] = []
    for result_path in sorted(corpus_root.glob("energyguide-samples/**/result.json")):
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("status") != "OBSERVED_SOURCE_PDF":
            continue
        sku = result.get("exact_sku")
        review = annotations.pop(sku, None)
        if review is None:
            raise ValueError(f"Missing review annotation for {sku}")
        candidates = json.loads((result_path.parent / "energyguide-field-candidates.json").read_text(encoding="utf-8"))
        layout = json.loads((result_path.parent / "energyguide-layout-candidates.json").read_text(encoding="utf-8"))
        if result.get("sha256") != review.get("pdf_sha256"):
            raise ValueError(f"Result/review PDF mismatch for {sku}")
        selected = select_annual_energy(candidates, layout, review)
        expected = review["expected_observation"]
        observed = selected["observation"]
        if observed["state"] != expected["state"]:
            raise ValueError(f"Unexpected observation state for {sku}")
        if observed["state"] == "VALUE" and observed["value"]["amount"] != expected["amount"]:
            raise ValueError(f"Unexpected annual energy value for {sku}")
        records.append({"exact_sku": sku, "pdf_sha256": result["sha256"], "observation": observed, "reason": selected["reason"]})
    if annotations:
        raise ValueError(f"Annotation has no preserved corpus result: {sorted(annotations)}")
    selected_count = sum(record["observation"]["state"] == "VALUE" for record in records)
    return {"status": "PASS", "reviewed_skus": len(records), "selected_skus": selected_count,
            "withheld_skus": len(records) - selected_count, "records": records}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.corpus_root, args.annotations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Replay current review annotations against a preserved G2 artifact ZIP."""

import argparse
import json
from pathlib import Path
import re
from typing import Any
import zipfile

from g2_label_activation import (
    load_capacity_review_annotations,
    load_review_annotations,
    select_live_reviewed_capacity,
    select_live_reviewed_energy,
    summarize_capacity_selection_outcomes,
    summarize_selection_outcomes,
)


CONTRACT = "G2_LABEL_ANNOTATION_REPLAY_V1"


def _one_json(archive: zipfile.ZipFile, suffix: str) -> dict[str, Any]:
    names = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise ValueError(f"Artifact must contain exactly one {suffix}")
    return json.loads(archive.read(names[0]))


def _json_by_hash(
    archive: zipfile.ZipFile, suffix: str
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    canonical: dict[str, str] = {}
    for name in archive.namelist():
        if "energyguide-samples/" not in name or not name.endswith(suffix):
            continue
        document = json.loads(archive.read(name))
        digest = document.get("pdf_sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Invalid PDF hash in {name}")
        serialized = json.dumps(document, sort_keys=True)
        if digest in canonical and canonical[digest] != serialized:
            raise ValueError(f"Byte-identical PDF has inconsistent {suffix}")
        indexed[digest] = document
        canonical[digest] = serialized
    return indexed


def replay(
    artifact_zip: Path,
    annual_review_path: Path,
    capacity_review_path: Path,
) -> dict[str, Any]:
    annual_reviews = load_review_annotations(annual_review_path)
    capacity_reviews = load_capacity_review_annotations(capacity_review_path)
    with zipfile.ZipFile(artifact_zip) as archive:
        checkpoint = _one_json(archive, "/checkpoint.json")
        candidates_by_hash = _json_by_hash(archive, "/energyguide-field-candidates.json")
        layouts_by_hash = _json_by_hash(archive, "/energyguide-layout-candidates.json")

    source_records = checkpoint.get("label_selection_summary", {}).get("records")
    if checkpoint.get("status") != "PASS" or not isinstance(source_records, list):
        raise ValueError("Successful source checkpoint label population is required")
    source_skus = {record.get("exact_sku") for record in source_records}
    if None in source_skus or len(source_skus) != len(source_records):
        raise ValueError("Source checkpoint exact-SKU population is invalid")
    unknown_reviews = (set(annual_reviews) | set(capacity_reviews)) - source_skus
    if unknown_reviews:
        raise ValueError(f"Review annotations are outside the source population: {sorted(unknown_reviews)}")

    annual_outcomes = []
    capacity_outcomes = []
    for source in source_records:
        sku = source["exact_sku"]
        digest = source.get("pdf_sha256")
        index = source.get("source_document_index")
        if not isinstance(digest, str) or digest not in candidates_by_hash or type(index) is not int:
            raise ValueError(f"Preserved candidates are unavailable for {sku}")
        result = {"sha256": digest}
        candidates = candidates_by_hash[digest]
        annual_review = annual_reviews.get(sku)
        if annual_review is None:
            annual_selection = select_live_reviewed_energy(
                sku, result, candidates, {}, annual_reviews
            )
        else:
            layout = layouts_by_hash.get(digest)
            if layout is None:
                raise ValueError(f"Preserved layout candidates are unavailable for reviewed {sku}")
            annual_selection = select_live_reviewed_energy(
                sku, result, candidates, layout, annual_reviews
            )
            expected = annual_review.get("expected_observation", {})
            observed = annual_selection["observation"]
            if observed.get("state") != expected.get("state"):
                raise ValueError(f"Annual review expectation differs for {sku}")
            if observed.get("state") == "VALUE" and observed["value"]["amount"] != expected.get("amount"):
                raise ValueError(f"Annual review amount differs for {sku}")
        capacity_selection = select_live_reviewed_capacity(
            sku, result, candidates, capacity_reviews
        )
        base = {
            "exact_sku": sku,
            "source_document_index": index,
            "pdf_sha256": digest,
        }
        annual_outcomes.append({**base, "selection": annual_selection})
        capacity_outcomes.append({**base, "selection": capacity_selection})

    return {
        "contract": CONTRACT,
        "status": "PASS",
        "source": {
            "artifact_zip": artifact_zip.name,
            "execution_run_id": checkpoint.get("run_id"),
        },
        "label_selection_summary": summarize_selection_outcomes(annual_outcomes),
        "capacity_selection_summary": summarize_capacity_selection_outcomes(capacity_outcomes),
        "overall_product_compliance": "NOT_EVALUATED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", type=Path)
    parser.add_argument("--annual-review", type=Path, required=True)
    parser.add_argument("--capacity-review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.artifact_zip, args.annual_review, args.capacity_review)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

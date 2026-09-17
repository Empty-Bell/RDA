"""Apply a saved visual review only to byte-identical live label observations."""

import json
from pathlib import Path
import re
from typing import Any

from g2_label_selection import select_annual_energy, select_capacity, unavailable


def load_review_annotations(path: Path) -> dict[str, dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("contract") != "MANUAL_VISUAL_REVIEW_BINDING_ONLY":
        raise ValueError("Unexpected review annotation contract")
    reviews: dict[str, dict[str, Any]] = {}
    for review in document.get("annotations", []):
        for sku in review.get("exact_skus", []):
            if not isinstance(sku, str) or not sku or sku in reviews:
                raise ValueError("Review annotation exact-SKU mapping is invalid")
            reviews[sku] = review
    if not reviews:
        raise ValueError("Review annotations are empty")
    return reviews


def load_capacity_review_annotations(path: Path) -> dict[str, dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("contract") != "CAPACITY_MODEL_REVIEW_PROJECTION_ONLY":
        raise ValueError("Unexpected capacity review annotation contract")
    reviews: dict[str, dict[str, Any]] = {}
    for review in document.get("records", []):
        for sku in review.get("exact_skus", []):
            if not isinstance(sku, str) or not sku or sku in reviews:
                raise ValueError("Capacity review exact-SKU mapping is invalid")
            reviews[sku] = review
    if not reviews:
        raise ValueError("Capacity review annotations are empty")
    return reviews


def select_live_reviewed_energy(
    exact_sku: str,
    result: dict[str, Any],
    candidates: dict[str, Any],
    layout: dict[str, Any],
    reviews: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Never carry a review forward when current collection bytes differ."""
    review = reviews.get(exact_sku)
    if review is None:
        return unavailable("NO_SAVED_REVIEW_ANNOTATION")
    if result.get("sha256") != review.get("pdf_sha256"):
        return unavailable("REVIEW_ARTIFACT_PDF_DOES_NOT_MATCH_CURRENT_COLLECTION")
    return select_annual_energy(candidates, layout, review)


def select_live_reviewed_capacity(
    exact_sku: str,
    result: dict[str, Any],
    candidates: dict[str, Any],
    reviews: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Never carry a capacity review forward when current PDF bytes differ."""
    review = reviews.get(exact_sku)
    if review is None:
        return unavailable("NO_SAVED_CAPACITY_REVIEW_ANNOTATION")
    if result.get("sha256") != review.get("pdf_sha256"):
        return unavailable("CAPACITY_REVIEW_PDF_DOES_NOT_MATCH_CURRENT_COLLECTION")
    return select_capacity(candidates, review)


def summarize_selection_outcomes(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    """Expose collection observations without implying an assessment result."""
    records = []
    seen = set()
    for outcome in outcomes:
        sku = outcome.get("exact_sku")
        index = outcome.get("source_document_index")
        digest = outcome.get("pdf_sha256")
        selection = outcome.get("selection")
        if (not isinstance(sku, str) or not sku or type(index) is not int
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or not isinstance(selection, dict) or not isinstance(selection.get("observation"), dict)
                or not isinstance(selection.get("reason"), str)):
            raise ValueError("Invalid label selection summary input")
        key = (sku, index)
        if key in seen:
            raise ValueError("Duplicate label selection summary record")
        seen.add(key)
        observation = selection["observation"]
        state = observation.get("state")
        if state not in {"VALUE", "NOT_OBSERVED"}:
            raise ValueError("Unexpected label selection observation state")
        records.append({"exact_sku": sku, "source_document_index": index, "pdf_sha256": digest,
                        "annual_energy_observation": observation, "selection_reason": selection["reason"]})
    records.sort(key=lambda item: (item["exact_sku"], item["source_document_index"]))
    selected = sum(item["annual_energy_observation"]["state"] == "VALUE" for item in records)
    return {"contract": "REVIEW_BOUND_LIVE_OBSERVATION_ONLY", "records": records,
            "counts": {"VALUE": selected, "NOT_OBSERVED": len(records) - selected}}


def summarize_capacity_selection_outcomes(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    """Expose reviewed capacity observations without adding an identity conclusion."""
    records = []
    seen = set()
    for outcome in outcomes:
        sku, index, digest, selection = (outcome.get(name) for name in
            ("exact_sku", "source_document_index", "pdf_sha256", "selection"))
        if (not isinstance(sku, str) or not sku or type(index) is not int
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or not isinstance(selection, dict) or not isinstance(selection.get("observation"), dict)
                or not isinstance(selection.get("reason"), str)):
            raise ValueError("Invalid capacity selection summary input")
        key = (sku, index)
        if key in seen:
            raise ValueError("Duplicate capacity selection summary record")
        seen.add(key)
        observation = selection["observation"]
        if observation.get("state") not in {"VALUE", "NOT_OBSERVED"}:
            raise ValueError("Unexpected capacity selection observation state")
        records.append({"exact_sku": sku, "source_document_index": index, "pdf_sha256": digest,
                        "capacity_observation": observation, "selection_reason": selection["reason"]})
    records.sort(key=lambda item: (item["exact_sku"], item["source_document_index"]))
    selected = sum(item["capacity_observation"]["state"] == "VALUE" for item in records)
    return {"contract": "REVIEW_BOUND_LIVE_CAPACITY_OBSERVATION_ONLY", "records": records,
            "counts": {"VALUE": selected, "NOT_OBSERVED": len(records) - selected}}

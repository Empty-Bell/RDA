"""Apply a saved visual review only to byte-identical live label observations."""

import json
from pathlib import Path
import re
from typing import Any

from g2_label_selection import (
    select_annual_energy,
    select_annual_energy_strict,
    select_capacity,
    select_capacity_strict,
    unavailable,
)


def observe_raw_model(candidates: dict[str, Any]) -> dict[str, Any]:
    """Project one parser token only; never normalize, correct, or match identity."""
    digest = candidates.get("pdf_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid raw model candidate PDF hash")
    models = candidates.get("model_candidates_raw")
    if not isinstance(models, list):
        raise ValueError("Invalid raw model candidates")
    if len(models) != 1 or not isinstance(models[0], dict):
        return unavailable("MISSING_OR_AMBIGUOUS_RAW_MODEL_CANDIDATE")
    value = models[0].get("value_raw")
    if not isinstance(value, str) or not value:
        return unavailable("MISSING_OR_AMBIGUOUS_RAW_MODEL_CANDIDATE")
    return {
        "observation": {"state": "VALUE", "value": value, "error": None},
        "reason": "UNIQUE_RAW_MODEL_CANDIDATE_NO_IDENTITY_MATCHING",
        "candidate": models[0],
    }


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
    """Use matching visual review, otherwise apply the strict source rule."""
    if result.get("sha256") != candidates.get("pdf_sha256"):
        return unavailable("CURRENT_RESULT_AND_CANDIDATES_PDF_DO_NOT_MATCH")
    review = reviews.get(exact_sku)
    if review is None:
        return select_annual_energy_strict(candidates, layout)
    if result.get("sha256") == review.get("pdf_sha256"):
        return select_annual_energy(candidates, layout, review)
    return select_annual_energy_strict(candidates, layout)


def select_live_reviewed_capacity(
    exact_sku: str,
    result: dict[str, Any],
    candidates: dict[str, Any],
    reviews: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Use matching visual review, otherwise apply the strict source rule."""
    if result.get("sha256") != candidates.get("pdf_sha256"):
        return unavailable("CURRENT_RESULT_AND_CANDIDATES_PDF_DO_NOT_MATCH")
    review = reviews.get(exact_sku)
    if review is None:
        return select_capacity_strict(candidates)
    if result.get("sha256") == review.get("pdf_sha256"):
        return select_capacity(candidates, review)
    return select_capacity_strict(candidates)


def summarize_selection_outcomes(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    """Expose collection observations without implying an assessment result."""
    records = []
    seen = set()
    for outcome in outcomes:
        sku = outcome.get("exact_sku")
        index = outcome.get("source_document_index")
        digest = outcome.get("pdf_sha256")
        selection = outcome.get("selection")
        if (
            not isinstance(sku, str)
            or not sku
            or type(index) is not int
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or not isinstance(selection, dict)
            or not isinstance(selection.get("observation"), dict)
            or not isinstance(selection.get("reason"), str)
        ):
            raise ValueError("Invalid label selection summary input")
        key = (sku, index)
        if key in seen:
            raise ValueError("Duplicate label selection summary record")
        seen.add(key)
        observation = selection["observation"]
        state = observation.get("state")
        if state not in {"VALUE", "NOT_OBSERVED"}:
            raise ValueError("Unexpected label selection observation state")
        records.append(
            {
                "exact_sku": sku,
                "source_document_index": index,
                "pdf_sha256": digest,
                "annual_energy_observation": observation,
                "selection_reason": selection["reason"],
            }
        )
    records.sort(key=lambda item: (item["exact_sku"], item["source_document_index"]))
    selected = sum(item["annual_energy_observation"]["state"] == "VALUE" for item in records)
    return {
        "contract": "STRICT_SOURCE_OR_HASH_REVIEW_OBSERVATION_V1",
        "records": records,
        "counts": {"VALUE": selected, "NOT_OBSERVED": len(records) - selected},
    }


def summarize_capacity_selection_outcomes(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    """Expose reviewed capacity observations without adding an identity conclusion."""
    records = []
    seen = set()
    for outcome in outcomes:
        sku, index, digest, selection = (
            outcome.get(name)
            for name in ("exact_sku", "source_document_index", "pdf_sha256", "selection")
        )
        if (
            not isinstance(sku, str)
            or not sku
            or type(index) is not int
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or not isinstance(selection, dict)
            or not isinstance(selection.get("observation"), dict)
            or not isinstance(selection.get("reason"), str)
        ):
            raise ValueError("Invalid capacity selection summary input")
        key = (sku, index)
        if key in seen:
            raise ValueError("Duplicate capacity selection summary record")
        seen.add(key)
        observation = selection["observation"]
        if observation.get("state") not in {"VALUE", "NOT_OBSERVED"}:
            raise ValueError("Unexpected capacity selection observation state")
        records.append(
            {
                "exact_sku": sku,
                "source_document_index": index,
                "pdf_sha256": digest,
                "capacity_observation": observation,
                "selection_reason": selection["reason"],
            }
        )
    records.sort(key=lambda item: (item["exact_sku"], item["source_document_index"]))
    selected = sum(item["capacity_observation"]["state"] == "VALUE" for item in records)
    return {
        "contract": "STRICT_SOURCE_OR_HASH_REVIEW_CAPACITY_OBSERVATION_V1",
        "records": records,
        "counts": {"VALUE": selected, "NOT_OBSERVED": len(records) - selected},
    }

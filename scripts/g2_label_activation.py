"""Apply a saved visual review only to byte-identical live label observations."""

import json
from pathlib import Path
from typing import Any

from g2_label_selection import select_annual_energy, unavailable


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

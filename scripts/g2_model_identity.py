"""Fixture-only label-model review and diagnostic contract.

This module cannot correct OCR, establish SKU identity, or evaluate compliance.
"""

from datetime import datetime
import re
from typing import Any


SHA256 = re.compile(r"[0-9a-f]{64}")


def _valid_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_box(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 4
        and all(type(item) in (int, float) for item in value)
        and value[0] < value[2]
        and value[1] < value[3]
    )


def validate_model_review(annotation: dict[str, Any]) -> dict[str, Any]:
    """Validate review provenance without treating it as an identity conclusion."""
    required = {
        "contract",
        "pdf_sha256",
        "render_sha256",
        "reviewer_id",
        "reviewed_at",
        "page",
        "box",
        "raw_token",
        "visual_transcription",
    }
    if not isinstance(annotation, dict) or set(annotation) != required:
        raise ValueError("Invalid model review fields")
    if annotation["contract"] != "MODEL_VISUAL_REVIEW_EVIDENCE_V1":
        raise ValueError("Unexpected model review contract")
    for key in ("pdf_sha256", "render_sha256"):
        if not isinstance(annotation[key], str) or not SHA256.fullmatch(annotation[key]):
            raise ValueError("Invalid model review hash")
    if not _valid_text(annotation["reviewer_id"]):
        raise ValueError("Missing model reviewer")
    if (
        type(annotation["page"]) is not int
        or annotation["page"] < 0
        or not _valid_box(annotation["box"])
    ):
        raise ValueError("Invalid model review region")
    if not _valid_text(annotation["raw_token"]) or not _valid_text(
        annotation["visual_transcription"]
    ):
        raise ValueError("Missing model review text")
    try:
        reviewed_at = datetime.fromisoformat(annotation["reviewed_at"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ValueError("Invalid model review timestamp") from error
    if reviewed_at.tzinfo is None:
        raise ValueError("Model review timestamp requires timezone")
    return annotation


def diagnose_literal_model_equality(
    *, raw_token: str, product_model: str, pdf_sha256: str, review: dict[str, Any] | None
) -> dict[str, Any]:
    """Return an evidence diagnostic while withholding every identity conclusion."""
    if not _valid_text(raw_token) or not _valid_text(product_model):
        raise ValueError("Raw label and product model tokens are required")
    if not isinstance(pdf_sha256, str) or not SHA256.fullmatch(pdf_sha256):
        raise ValueError("Invalid label PDF hash")

    review_status = "NOT_REVIEWED"
    if review is not None:
        validate_model_review(review)
        if review["pdf_sha256"] != pdf_sha256 or review["raw_token"] != raw_token:
            review_status = "REVIEW_PROVENANCE_MISMATCH"
        else:
            review_status = "REVIEWED_SEPARATE_TRANSCRIPTION"

    if raw_token == product_model and "*" not in raw_token and "?" not in raw_token:
        diagnostic = "LITERAL_EQUALITY_DIAGNOSTIC_ONLY"
    elif "*" in raw_token or "?" in raw_token or "*" in product_model or "?" in product_model:
        diagnostic = "WITHHELD_WILDCARD_SEMANTICS"
    elif product_model.casefold() in {
        raw_token.casefold() + "/aa",
        raw_token.casefold() + "aa",
    } or raw_token.casefold() in {
        product_model.casefold() + "/aa",
        product_model.casefold() + "aa",
    }:
        diagnostic = "WITHHELD_SUFFIX_OR_FORMAT_VARIATION"
    else:
        diagnostic = "WITHHELD_NONLITERAL_OR_CONFUSION_DIFFERENCE"

    return {
        "raw_token": raw_token,
        "product_model": product_model,
        "review_status": review_status,
        "identity_diagnostic": diagnostic,
        "identity_state": "NOT_EVALUATED",
        "correction_state": "NOT_APPLIED",
    }

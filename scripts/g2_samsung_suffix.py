"""User-approved Samsung terminal AA observation; never EPA identity matching."""

import re


EXACT_SKU = re.compile(r"[A-Z0-9]+(?:/AA|AA)")


def normalize_terminal_aa(exact_sku: str) -> dict:
    """Remove only the approved terminal AA or /AA suffix and retain all provenance."""
    if not isinstance(exact_sku, str) or not EXACT_SKU.fullmatch(exact_sku):
        raise ValueError("Unsupported Samsung exact SKU encoding")
    suffix = "/AA" if exact_sku.endswith("/AA") else "AA"
    normalized = exact_sku[: -len(suffix)]
    if not normalized:
        raise ValueError("Samsung exact SKU has no identifier before AA suffix")
    return {
        "exact_sku_raw": exact_sku,
        "normalized_identifier": normalized,
        "removed_terminal_suffix": suffix,
        "normalization_basis": "USER_APPROVED_SAMSUNG_TERMINAL_AA_V1",
        "identity_state": "NOT_EVALUATED",
        "assessment": "NOT_EVALUATED",
    }

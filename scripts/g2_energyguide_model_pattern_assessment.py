"""Compare every refrigerator EnergyGuide model token with its exact PDP SKU."""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from g2_samsung_suffix import normalize_terminal_aa
from energyguide_model_identity import matches_printed_model


CONTRACT = "G2_ENERGYGUIDE_MODEL_PREFIX_ASSESSMENT_V2"
REVIEW_CONTRACT = "CAPACITY_MODEL_REVIEW_PROJECTION_ONLY"
TOKEN = re.compile(r"[A-Z0-9][A-Z0-9*]*\Z")


def _tokens(raw: str) -> list[str]:
    """Keep every model in a model field, including line/comma/semicolon lists."""
    if not isinstance(raw, str):
        return []
    pieces = re.split(r"[,;\r\n]+", raw)
    values = [part.strip() for part in pieces]
    return list(dict.fromkeys(value for value in values if TOKEN.fullmatch(value)))


def _matches_prefix(pattern: str, identifier: str) -> bool:
    """Apply the approved shared printed-label/PDP model inclusion rule."""
    return matches_printed_model(pattern, identifier, strip_terminal_aa=True)


def build_assessment(bundle: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    run_id = bundle.get("manifest", {}).get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("Canonical bundle run ID is missing")
    if review.get("contract") != REVIEW_CONTRACT:
        raise ValueError("Model review contract is invalid")
    products = bundle.get("products")
    if not isinstance(products, list) or not products:
        raise ValueError("Canonical product population is missing")
    skus = [item.get("exact_sku") for item in products if isinstance(item, dict)]
    if len(skus) != len(products) or len(set(skus)) != len(skus):
        raise ValueError("Canonical product SKU population is invalid")
    facts = [item for item in bundle.get("facts", []) if item.get("kind") == "ENERGYGUIDE"]
    by_sku = {item.get("exact_sku"): item for item in facts}
    if len(by_sku) != len(facts) or set(by_sku) != set(skus):
        raise ValueError("EnergyGuide model facts do not cover the product population")

    reviewed = {}
    for group in review.get("records", []):
        if not isinstance(group, dict):
            raise ValueError("Model review record is invalid")
        for sku in group.get("exact_skus", []):
            if sku in reviewed:
                raise ValueError("Model review SKU is duplicated")
            reviewed[sku] = group

    records = []
    for sku in sorted(skus):
        observations = by_sku[sku].get("observations", {})
        model = observations.get("label_model_raw", {})
        document = observations.get("document_sha256", {})
        if model.get("state") != "VALUE" or document.get("state") != "VALUE":
            raise ValueError("Selected EnergyGuide model or PDF hash is unavailable")
        raw = model.get("value")
        sha256 = document.get("value")
        if not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", sha256):
            raise ValueError("EnergyGuide PDF hash is invalid")
        tokens = _tokens(raw)
        if not tokens:
            raise ValueError("Selected EnergyGuide model tokens are invalid")
        group = reviewed.get(sku)
        if group is not None:
            if group.get("pdf_sha256") != sha256:
                raise ValueError("Reviewed EnergyGuide PDF hash differs from live fact")
            reviewed_tokens = group.get("model_tokens_raw")
            if reviewed_tokens is not None and set(tokens) != set(reviewed_tokens):
                raise ValueError("Reviewed model tokens differ from live fact")
        normalized = normalize_terminal_aa(sku)
        identifier = normalized["normalized_identifier"]
        matches = [token for token in tokens if _matches_prefix(token, sku)]
        records.append({
            "exact_sku": sku,
            "normalized_identifier": identifier,
            "normalization": normalized,
            "label_pdf_sha256": sha256,
            "label_model_text": raw,
            "approved_patterns": tokens,
            "matching_patterns": matches,
            "display_outcome": "PASS" if matches else "NOT_EVALUATED",
            "assessment": "MODEL_PREFIX_INCLUDED" if matches else "MODEL_PREFIX_NOT_INCLUDED",
        })

    counts = Counter(record["display_outcome"] for record in records)
    return {
        "contract": CONTRACT,
        "status": "PASS",
        "source": {"execution_run_id": run_id, "review_projection_contract": REVIEW_CONTRACT},
        "scope": {
            "assessment_mode": "ALL_SELECTED_LABEL_MODEL_TOKENS_PREFIX_INCLUSION",
            "wildcard_grammar": "FIXED_POSITIONS_MATCH; TRAILING_STARS_MAY_BE_EMPTY_OR_COVER_PDP_SUFFIX",
            "suffix_rule": "ONLY_TERMINAL_AA_OR_SLASH_AA_REMOVAL",
        },
        "decision_rule": "PASS when any complete printed token matches the normalized PDP model prefix; unresolved tokens do not become a mismatch finding.",
        "counts": {"population": len(records), "display": {key: counts.get(key, 0) for key in ("PASS", "NOT_EVALUATED")}},
        "assessment_enabled": True,
        "overall_product_compliance": "NOT_EVALUATED",
        "records": records,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    args = parser.parse_args()
    result = build_assessment(json.loads(args.bundle.read_text(encoding="utf-8")), json.loads(args.review.read_text(encoding="utf-8")))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Assess only the reviewed EnergyGuide model-pattern groups approved for inclusion."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

from g2_samsung_suffix import normalize_terminal_aa


CONTRACT = "G2_ENERGYGUIDE_REVIEW_BOUND_MODEL_PATTERN_ASSESSMENT_V1"
REVIEW_KIND = "SOURCE_LABEL_EXPLICITLY_LISTS_TWO_PATTERNS_IDENTITY_NOT_EVALUATED"


def _matches(pattern: str, identifier: str) -> bool:
    """`*` means exactly one upper-case alphanumeric character in this reviewed slice."""
    if not isinstance(pattern, str) or not isinstance(identifier, str) or len(pattern) != len(identifier):
        return False
    return all(
        (token == "*" and value.isascii() and value.isalnum() and (value.isupper() or value.isdigit()) or token == value)
        for token, value in zip(pattern, identifier)
    )


def build_assessment(bundle: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    run_id = bundle.get("manifest", {}).get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("Canonical bundle run ID is missing")
    if review.get("contract") != "CAPACITY_MODEL_REVIEW_PROJECTION_ONLY":
        raise ValueError("Model review contract is invalid")
    records = []
    for group in review.get("records", []):
        if group.get("model_review") != REVIEW_KIND:
            continue
        pdf_sha256 = group.get("pdf_sha256")
        patterns = group.get("model_tokens_raw")
        skus = group.get("exact_skus")
        if (not isinstance(pdf_sha256, str) or not isinstance(patterns, list) or len(patterns) != 2
                or not all(isinstance(x, str) and x for x in patterns)
                or not isinstance(skus, list) or not skus):
            raise ValueError("Reviewed model-pattern group is malformed")
        for exact_sku in skus:
            normalized = normalize_terminal_aa(exact_sku)
            identifier = normalized["normalized_identifier"]
            matching = [pattern for pattern in patterns if _matches(pattern, identifier)]
            records.append({
                "exact_sku": exact_sku,
                "normalized_identifier": identifier,
                "normalization": normalized,
                "label_pdf_sha256": pdf_sha256,
                "label_model_text": group.get("model_text_raw"),
                "approved_patterns": patterns,
                "matching_patterns": matching,
                "display_outcome": "PASS" if matching else "NOT_EVALUATED",
                "assessment": "MODEL_PATTERN_INCLUDED" if matching else "MODEL_PATTERN_NOT_INCLUDED",
            })
    skus = [record["exact_sku"] for record in records]
    if not records or len(skus) != len(set(skus)):
        raise ValueError("Reviewed model-pattern SKU scope is invalid")
    counts = Counter(record["display_outcome"] for record in records)
    return {
        "contract": CONTRACT,
        "status": "PASS",
        "source": {"execution_run_id": run_id, "review_projection_contract": review["contract"]},
        "scope": {
            "assessment_mode": "REVIEW_BOUND_TWO_PATTERN_INCLUSION_ONLY",
            "wildcard_grammar": "STAR_MATCHES_EXACTLY_ONE_UPPERCASE_ALPHANUMERIC_CHARACTER",
            "reviewed_label_hashes_only": sorted({record["label_pdf_sha256"] for record in records}),
        },
        "decision_rule": "PASS when one explicitly reviewed label pattern matches after approved terminal AA removal; no broader model matching is enabled.",
        "counts": {"population": len(records), "display": {key: counts.get(key, 0) for key in ("PASS", "NOT_EVALUATED")}},
        "assessment_enabled": True,
        "overall_product_compliance": "NOT_EVALUATED",
        "records": sorted(records, key=lambda item: item["exact_sku"]),
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

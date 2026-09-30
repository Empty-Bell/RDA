"""Compare PDP exact SKU, raw EnergyGuide patterns, and current EPA models."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from energyguide_model_identity import matches_printed_model


def exact(value):
    value = re.sub(r"[^A-Z0-9]", "", str(value).upper())
    return value[:-2] if value.endswith("AA") else value


def pattern(value):
    value = re.sub(r"[^A-Z0-9*?]", "", str(value).upper())
    return value[:-2] if value.endswith("AA") else value


def matches_exact(model_pattern, identifier):
    model_pattern, identifier = pattern(model_pattern), exact(identifier)
    return bool(model_pattern and len(model_pattern) == len(identifier) and all(
        token in "*?" or token == value for token, value in zip(model_pattern, identifier)
    ))


def patterns_overlap(first, second):
    first, second = pattern(first), pattern(second)
    return bool(first and len(first) == len(second) and all(
        left in "*?" or right in "*?" or left == right for left, right in zip(first, second)
    ))


def split_patterns(value):
    """Split model lists while keeping model-internal hyphens and slashes."""
    if not isinstance(value, str):
        return []
    parts = []
    for line in value.splitlines() or [value]:
        # "Models" is a heading, while model identifiers can follow on the
        # same line or on the next lines. Strip the heading only.
        line = re.sub(r"^\s*models?\s*[:=]?\s*", "", line, flags=re.I)
        parts.extend(part.strip() for part in re.split(r"[,;|]+", line) if part.strip())
    return parts


def candidate_values(rows):
    """Keep every raw parser token, including lists packed into one token."""
    values = []
    for row in rows or []:
        raw = row.get("value_raw") if isinstance(row, dict) else row
        values.extend(split_patterns(raw))
    return sorted(set(values))


def unique_values(rows, key):
    values = []
    for row in rows or []:
        raw = row.get(key) if isinstance(row, dict) else row
        values.extend(split_patterns(raw))
    return sorted(set(values))


def relation(left, right, comparator):
    if not left or not right:
        return "NOT_COMPARABLE"
    return "EQUAL" if any(comparator(a, b) for a in left for b in right) else "DIFFERENT"


def build(package, out):
    source = json.loads(Path(package).read_bytes())
    rows = []
    for item in source.get("rows", []):
        sku = item["exact_sku"]
        raw_labels = candidate_values(item.get("energyguide_model_candidates_raw", []))
        reviewed_labels = candidate_values(item.get("energyguide_model_patterns_visual_reviewed", []))
        labels = reviewed_labels or raw_labels
        epa = unique_values(item.get("epa_candidates_raw", []), "model_number")
        pdp_label = relation([sku], labels, lambda a, b: matches_printed_model(b, a, strip_terminal_aa=True))
        pdp_epa = ("EQUAL" if item.get("epa_match_status") == "MATCHED_CURRENT_EPA_FAMILY_PATTERN" and epa
                   else relation([sku], epa, lambda a, b: matches_exact(b, a)))
        label_epa = ("EQUAL" if pdp_label == "EQUAL" and pdp_epa == "EQUAL"
                     else relation(labels, epa, patterns_overlap))
        rows.append({
            "exact_sku": sku,
            "pdp_model_exact_sku": sku,
            "normalized_pdp_model": exact(sku),
            "energyguide_model_patterns_raw": labels,
            "energyguide_model_patterns_ocr_raw": raw_labels,
            "energyguide_model_patterns_visual_reviewed": reviewed_labels,
            "energyguide_model_pattern_source": "HUMAN_VISUAL_REVIEW" if reviewed_labels else "RAW_OCR",
            "epa_current_model_candidates_raw": epa,
            "pdp_vs_energyguide_model": pdp_label,
            "pdp_vs_epa_model": pdp_epa,
            "energyguide_vs_epa_model": label_epa,
            "matching_energyguide_patterns": [x for x in labels if matches_printed_model(x, sku, strip_terminal_aa=True)],
            "assessment": "NOT_EVALUATED",
        })
    comparisons = ("pdp_vs_energyguide_model", "pdp_vs_epa_model", "energyguide_vs_epa_model")
    report = {
        "contract": "G3_DISHWASHER_MODEL_COMPARISON_V2", "status": "PASS",
        "source_bundle_fingerprint": source.get("source_bundle_fingerprint"),
        "source_package_sha256": hashlib.sha256(Path(package).read_bytes()).hexdigest(),
        "scope": "PDP exact SKU, raw EnergyGuide model patterns, and current EPA candidate model comparison only; no severity or compliance assessment",
        "counts": {name: {state: sum(row[name] == state for row in rows) for state in ("EQUAL", "DIFFERENT", "NOT_COMPARABLE")} for name in comparisons},
        "records": rows,
    }
    destination = Path(out); destination.mkdir(parents=True, exist_ok=True)
    (destination / "model-comparison.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "sku_count": len(rows), "counts": report["counts"]}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build(args.package, args.out)

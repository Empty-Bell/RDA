"""Compare PDP exact SKU, raw EnergyGuide patterns, and current EPA models."""

import argparse
import json
import re
from pathlib import Path


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


def relation(left, right, comparator):
    if not left or not right:
        return "NOT_COMPARABLE"
    return "EQUAL" if any(comparator(a, b) for a in left for b in right) else "DIFFERENT"


def build(package, out):
    source = json.loads(Path(package).read_bytes())
    rows = []
    for item in source.get("rows", []):
        sku = item["exact_sku"]
        labels = sorted({x.get("value_raw") for x in item.get("energyguide_model_candidates_raw", []) if isinstance(x.get("value_raw"), str)})
        epa = sorted({x.get("model_number") for x in item.get("epa_candidates_raw", []) if isinstance(x.get("model_number"), str)})
        pdp_label = relation([sku], labels, lambda a, b: matches_exact(b, a))
        pdp_epa = relation([sku], epa, lambda a, b: matches_exact(b, a))
        label_epa = relation(labels, epa, patterns_overlap)
        rows.append({
            "exact_sku": sku,
            "pdp_model_exact_sku": sku,
            "normalized_pdp_model": exact(sku),
            "energyguide_model_patterns_raw": labels,
            "epa_current_model_candidates_raw": epa,
            "pdp_vs_energyguide_model": pdp_label,
            "pdp_vs_epa_model": pdp_epa,
            "energyguide_vs_epa_model": label_epa,
            "matching_energyguide_patterns": [x for x in labels if matches_exact(x, sku)],
            "assessment": "NOT_EVALUATED",
        })
    comparisons = ("pdp_vs_energyguide_model", "pdp_vs_epa_model", "energyguide_vs_epa_model")
    report = {
        "contract": "G3_DISHWASHER_MODEL_COMPARISON_V2", "status": "PASS",
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

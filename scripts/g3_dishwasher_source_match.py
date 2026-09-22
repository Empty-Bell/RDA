"""Project exact dishwasher SKUs to current EPA literal and positional-pattern rows."""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def j(path):
    return json.loads(Path(path).read_bytes())


def normalize_identifier(value):
    """Apply the approved terminal-AA normalization without altering raw evidence."""
    value = re.sub(r"[^A-Z0-9]", "", str(value or "").upper())
    return value[:-2] if value.endswith("AA") else value


def normalize_pattern(value):
    value = re.sub(r"[^A-Z0-9*?]", "", str(value or "").upper())
    return value[:-2] if value.endswith("AA") else value


def positional_pattern_matches(pattern, exact_sku):
    """`*` and `?` each match one upper-case alphanumeric position only."""
    pattern, exact_sku = normalize_pattern(pattern), normalize_identifier(exact_sku)
    if not pattern or not exact_sku or len(pattern) != len(exact_sku):
        return False
    return all(token in "*?" or token == character for token, character in zip(pattern, exact_sku))


def row_reference(row):
    return {"pd_id": row.get("pd_id"), "model_number_raw": row.get("model_number"),
            "normalized_model_identifier": normalize_identifier(row.get("model_number"))}


def build(observation_root, epa_root, out):
    obs = j(Path(observation_root) / "sku-document-index.json")
    epa = j(Path(epa_root) / "samsung-current-rows.json")
    if not isinstance(epa, list):
        raise ValueError("EPA rows are not a list")
    literal_rows, positional_rows, unsupported_pattern_rows = {}, [], []
    for row in epa:
        model = row.get("model_number")
        if not isinstance(model, str) or not model:
            continue
        reference = row_reference(row)
        if "*" in model or "?" in model:
            positional_rows.append((model, reference))
        elif "#" in model:
            unsupported_pattern_rows.append(reference)
        else:
            literal_rows.setdefault(normalize_identifier(model), []).append(reference)
    skus = sorted({x["exact_sku"] for x in obs.get("sku_documents", [])})
    rows = []
    for sku in skus:
        normalized_sku = normalize_identifier(sku)
        literal_candidates = literal_rows.get(normalized_sku, [])
        pattern_candidates = [reference for pattern, reference in positional_rows if positional_pattern_matches(pattern, sku)]
        if literal_candidates:
            candidates, state = literal_candidates, "MATCHED_CURRENT_EPA_ROW" if len(literal_candidates) == 1 else "AMBIGUOUS_CURRENT_EPA_ROWS"
        elif pattern_candidates:
            candidates, state = pattern_candidates, "MATCHED_CURRENT_EPA_PATTERN_CANDIDATES" if len(pattern_candidates) == 1 else "AMBIGUOUS_CURRENT_EPA_ROWS"
        elif unsupported_pattern_rows:
            candidates, state = [], "UNRESOLVED_CURRENT_EPA_PATTERN_ENCODING"
        else:
            candidates, state = [], "NO_CURRENT_EPA_ROW"
        rows.append({"exact_sku": sku, "normalized_sku": normalized_sku,
                     "literal_candidates": literal_candidates, "positional_pattern_candidates": pattern_candidates,
                     "unsupported_pattern_references": unsupported_pattern_rows, "candidate_count": len(candidates),
                     "candidate_pd_ids": [x["pd_id"] for x in candidates],
                     "candidate_model_numbers": [x["model_number_raw"] for x in candidates],
                     "match_status": state, "assessment": "NOT_EVALUATED"})
    states = ("MATCHED_CURRENT_EPA_ROW", "MATCHED_CURRENT_EPA_PATTERN_CANDIDATES", "NO_CURRENT_EPA_ROW",
              "AMBIGUOUS_CURRENT_EPA_ROWS", "UNRESOLVED_CURRENT_EPA_PATTERN_ENCODING")
    report = {"contract": "G3_DISHWASHER_CURRENT_EPA_MATCH_V2", "created_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Exact SKU to current EPA literal or approved positional-pattern candidates only; no certification or compliance assessment",
              "pattern_grammar": "STAR_OR_QUESTION_MATCHES_EXACTLY_ONE_UPPERCASE_ALPHANUMERIC_CHARACTER",
              "status": "PASS", "sku_count": len(rows), "epa_row_count": len(epa),
              "counts": {state: sum(x["match_status"] == state for x in rows) for state in states}, "rows": rows}
    Path(out).mkdir(parents=True, exist_ok=True)
    Path(out, "match-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", **report["counts"]}, sort_keys=True))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--observation-root", required=True)
    p.add_argument("--epa-root", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    build(a.observation_root, a.epa_root, a.out)

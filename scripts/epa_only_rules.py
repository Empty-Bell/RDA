"""Shared, source-independent rules for EPA-only ENERGY STAR product groups."""

import re


TRUE_VALUES = {"yes", "y", "true", "1"}
FALSE_VALUES = {"no", "n", "false", "0"}
MODEL_PATTERN = re.compile(r"[A-Z0-9*/./-]+\Z", re.I)
LOW_ISSUE = "SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT"
HIGH_ISSUE = "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE"
known_non_us

def model_pattern_candidate(pattern, exact_sku):
    """Return a reviewable current-EPA identity candidate, never a fuzzy match.

    EPA's positional `*` occupies exactly one A-Z/0-9 position. If the EPA
    family pattern ends before a Samsung SKU suffix (for example `AA`), that
    suffix is retained as evidence and does not invalidate the candidate.
    """
    if not isinstance(pattern, str) or not MODEL_PATTERN.fullmatch(pattern):
        return None
    if not isinstance(exact_sku, str) or not exact_sku:
        return None
    pattern_upper, sku_upper = pattern.upper(), exact_sku.upper()
    if "*" not in pattern_upper:
        if pattern_upper != sku_upper:
            return None
    else:
        if len(pattern_upper) > len(sku_upper):
            return None
        expression = "^" + "".join(
            "[A-Z0-9]" if char == "*" else re.escape(char)
            for char in pattern_upper
        )
        if not re.match(expression, sku_upper):
            return None
    matched_length = len(pattern_upper)
    return {
        "model_pattern_raw": pattern,
        "exact_sku_raw": exact_sku,
        "candidate_basis": "LITERAL_EXACT" if "*" not in pattern else
            "POSITIONAL_PREFIX_PATTERN; EACH * = ONE A-Z/0-9 CHARACTER",
        "matched_prefix_raw": exact_sku[:matched_length],
        "remaining_sku_suffix_raw": exact_sku[matched_length:],
    }


def flag_state(value):
    normalized = str(value).strip().lower() if value is not None else ""
    if normalized in TRUE_VALUES:
        return "PRESENT"
    if normalized in FALSE_VALUES:
        return "ABSENT"
    return "UNKNOWN"


def publication_points(claim):
    """Interpret explicit claim observations at PLP, PDP logo, and visible specs."""
    claim = claim if isinstance(claim, dict) else {}

    plp_raw = claim.get("plp_energy_star_flag_raw")
    plp_state = flag_state(plp_raw)

    pdp_badges = claim.get("rendered_attributed_badges_raw")
    pdp_inspection = claim.get("pdp_logo_inspection_raw")
    if isinstance(pdp_badges, list) and pdp_badges:
        pdp_state = "PRESENT"
    elif pdp_inspection == "SUPPORTED_PRIMARY_SURFACE_COMPLETE":
        pdp_state = "ABSENT"
    else:
        pdp_state = "UNKNOWN"

    visible_specs = claim.get("pdp_visible_spec_energy_star_rows_raw")
    spec_inspection = claim.get("pdp_spec_surface_inspection_raw")
    # Bridge Data is the authoritative structured Specs surface.  Use it when
    # the rendered DOM table is not mounted; an empty, complete projected list
    # is an observed absence rather than an unknown value.
    bridge_specs = claim.get("pdp_spec_energy_star_claim_raw")
    if (not isinstance(visible_specs, list) or not visible_specs) and isinstance(bridge_specs, list):
        visible_specs = bridge_specs
        spec_inspection = "SUPPORTED_BRIDGE_SPEC_TABLE_COMPLETE"
    if isinstance(visible_specs, list) and visible_specs:
        observed_states = []
        for row in visible_specs:
            if not isinstance(row, dict):
                observed_states.append("UNKNOWN")
                continue
            cells = row.get("cells") if isinstance(row.get("cells"), list) else []
            text = " ".join(str(value) for value in
                            [row.get("text"), row.get("name"), row.get("value"), *cells]
                            if value is not None)
            raw_value = cells[-1] if len(cells) > 1 else row.get("value")
            final_cell = str(raw_value).strip().lower() if raw_value is not None else ""
            if (final_cell in FALSE_VALUES or re.search(r"\bnot\s+(?:energy\s+star|certified)\b", text, re.I)):
                observed_states.append("ABSENT")
            elif final_cell in TRUE_VALUES or re.search(r"\benergy\s+star\b", text, re.I):
                observed_states.append("PRESENT")
            else:
                observed_states.append("UNKNOWN")
        if observed_states and set(observed_states) == {"PRESENT"}:
            spec_state = "PRESENT"
        elif observed_states and set(observed_states) == {"ABSENT"}:
            spec_state = "ABSENT"
        else:
            spec_state = "UNKNOWN"
    elif spec_inspection in ("SUPPORTED_VISIBLE_SPEC_TABLE_COMPLETE", "SUPPORTED_BRIDGE_SPEC_TABLE_COMPLETE"):
        spec_state = "ABSENT"
    else:
        spec_state = "UNKNOWN"

    return {
        "plp_logo": {"state": plp_state, "raw_value": plp_raw},
        "pdp_logo": {"state": pdp_state, "inspection": pdp_inspection,
                     "attributed_badges_raw": pdp_badges or []},
        "spec_certification": {"state": spec_state, "inspection": spec_inspection,
                               "visible_rows_raw": visible_specs or []},
    }


def publication_assessment(epa_registration, points):
    states = [item["state"] for item in points.values()]
    if epa_registration == "PRESENT":
        if all(state == "PRESENT" for state in states):
            return "PASS", []
        if "ABSENT" in states:
            return "LOW", [{"control": "ENERGY_STAR_PUBLICATION", "severity": "LOW",
                            "issue_code": LOW_ISSUE}]
        return "NOT_EVALUATED", []
    if epa_registration == "ABSENT":
        if "PRESENT" in states:
            return "HIGH", [{"control": "ENERGY_STAR_PUBLICATION", "severity": "HIGH",
                             "issue_code": HIGH_ISSUE}]
        if all(state == "ABSENT" for state in states):
            return "NO_FINDING", []
    return "NOT_EVALUATED", []


def us_market_state(value):
    """Recognize an explicit United States market without guessing on blanks."""
    if isinstance(value, (list, tuple, set)):
        value = ", ".join(str(item) for item in value)
    elif isinstance(value, dict):
        value = ", ".join(str(item) for item in value.values())
    if not isinstance(value, str) or not value.strip():
        return "UNKNOWN"
    upper = value.upper()
    if (re.search(r"(?<![A-Z])UNITED\s+STATES(?![A-Z])", upper)
            or re.search(r"(?<![A-Z])U\.?S\.?A?\.?(?![A-Z])", upper)):
        return "US"
    tokens = [re.sub(r"[^A-Z]", "", token) for token in re.split(r"[,;/|]|\band\b", upper)]
    tokens = [token for token in tokens if token]
    known_non_us = {"CANADA", "CA", "MEXICO", "MX", "JAPAN", "JP", "AUSTRALIA", "AU"}
    if tokens and all(token in known_non_us for token in tokens):
        return "OUTSIDE_US"
    return "UNKNOWN"


def epa_registration_state(dryer_candidates, combo_candidates):
    candidates = [*dryer_candidates, *combo_candidates]
    markets = [us_market_state(row.get("markets_raw")) for row in candidates]
    if "US" in markets:
        state = "PRESENT"
    elif not candidates or all(value == "OUTSIDE_US" for value in markets):
        state = "ABSENT"
    else:
        state = "UNKNOWN"
    return state, markets


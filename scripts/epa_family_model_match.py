"""Conservative Samsung SKU inclusion in a current ENERGY STAR family row."""

from decimal import Decimal, InvalidOperation
import re


MIN_FIXED_PREFIX = 8


def normalized_sku(sku):
    raw = str(sku or "").upper()
    if not re.fullmatch(r"[A-Z0-9]+(?:/AA|AA)", raw):
        return None
    return raw[:-3] if raw.endswith("/AA") else raw[:-2]


def annual_number(value):
    if value is None:
        return None
    raw = str(value).strip()
    match = re.search(r"(?<![\d.])(\d+(?:\.\d+)?)\s*kwh\s*/\s*(?:year|yr)\b", raw, re.I)
    if match:
        raw = match.group(1)
    elif not re.fullmatch(r"\d+(?:\.\d+)?", raw):
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def include(sku, row, *, annual_values=(), allow_trailing_star_group=False):
    """Return a supported match kind, or None when any identity gate is absent.

    The relaxed case is confined to a literal prefix plus trailing stars.  It
    requires an independent annual-kWh corroboration.  Internal fixed letters
    after a wildcard, short prefixes, non-US rows and unknown annual units do
    not become registrations through this path.
    """
    identifier = normalized_sku(sku)
    model = str(row.get("model_number") or "").upper()
    if (not identifier or not re.fullmatch(r"[A-Z0-9*#]+", model)
            or str(row.get("brand_name") or "").upper() != "SAMSUNG"
            or "UNITED STATES" not in str(row.get("markets") or "").upper()
            or not (row.get("date_certified") or row.get("date_qualified"))
            or not str(row.get("pd_id") or "").isdigit()):
        return None
    fixed = re.split(r"[*#]", model, maxsplit=1)[0]
    if len(fixed) < MIN_FIXED_PREFIX or not identifier.startswith(fixed):
        return None
    if len(model) == len(identifier) and all(
        (token == "*" and char.isalnum())
        or (token == "#" and char.isdigit())
        or token == char
        for token, char in zip(model, identifier)
    ):
        return "POSITIONAL_PATTERN"
    if not allow_trailing_star_group or not re.fullmatch(r"[A-Z0-9]{8,}\*+", model):
        return None
    official_energy = annual_number(row.get("annual_energy_use_kwh_year") or row.get("annual_energy_use_kwh_yr"))
    independently_observed = {annual_number(value) for value in annual_values}
    independently_observed.discard(None)
    if official_energy is None or official_energy not in independently_observed:
        return None
    return "TRAILING_STAR_MODEL_GROUP_AND_ANNUAL_ENERGY"


def unique_supported_rows(sku, rows, *, annual_values=(), allow_trailing_star_group=False):
    matches = []
    for row in rows:
        kind = include(sku, row, annual_values=annual_values,
                       allow_trailing_star_group=allow_trailing_star_group)
        if kind:
            matches.append({"match_kind": kind, "source_row": row})
    # Conflicting official values cannot be silently collapsed into PASS.
    energies = {annual_number(item["source_row"].get("annual_energy_use_kwh_year")
                              or item["source_row"].get("annual_energy_use_kwh_yr")) for item in matches}
    return matches if len(energies) <= 1 else []

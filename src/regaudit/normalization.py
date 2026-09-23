"""Source encoding normalization only; no comparisons or certification decisions."""

import math
import re
from typing import Any


def absent(reason: str, raw: Any) -> dict[str, Any]:
    return {
        "observation": {"state": "NOT_OBSERVED", "value": None, "error": None},
        "reason": reason,
        "raw": raw,
    }


def observed(value: Any, raw: Any) -> dict[str, Any]:
    return {
        "observation": {"state": "VALUE", "value": value, "error": None},
        "reason": "EXPLICIT_SOURCE_ENCODING",
        "raw": raw,
    }


def claim(values: list[Any]) -> dict[str, Any]:
    if not values:
        return absent("SOURCE_CHANNEL_UNOBSERVED", values)
    parsed = []
    for value in values:
        if type(value) is bool:
            parsed.append(value)
        elif isinstance(value, str) and value.strip().lower() in ("y", "yes", "true"):
            parsed.append(True)
        elif isinstance(value, str) and value.strip().lower() in ("n", "no", "false"):
            parsed.append(False)
        else:
            return absent("UNRECOGNIZED_OR_NULL_FLAG", values)
    if len(set(parsed)) != 1:
        return absent("CONFLICTING_FLAGS_WITHIN_SOURCE_CHANNEL", values)
    return observed(parsed[0], values)


def measurement(
    entries: list[dict[str, Any]],
    kind: str,
    *,
    allow_refrigerator_energy_rows: bool = False,
) -> dict[str, Any]:
    if kind not in ("annual_energy", "capacity"):
        raise ValueError("Unknown measurement kind")
    if not entries or (
        kind == "annual_energy" and len(entries) != 1 and not allow_refrigerator_energy_rows
    ):
        return absent("MISSING_OR_MULTIPLE_MEASUREMENTS", entries)
    number = r"(\d+(?:\.\d+)?)"
    if kind == "annual_energy":
        parsed = []
        for source in entries:
            name, value = source.get("name"), source.get("value")
            if not isinstance(name, str) or not isinstance(value, str):
                return absent("UNSUPPORTED_MEASUREMENT_ENCODING", entries)
            pattern = number + r"\s*kWh\s*/\s*(?:yr|year)"
            if allow_refrigerator_energy_rows and name == "Energy Consumption":
                pattern = number + r"\s*kWh(?:\s*/\s*(?:yr|year))?"
            match = re.fullmatch(pattern, value.strip(), re.I)
            if match is None:
                return absent("AMBIGUOUS_NUMBER_OR_UNIT", entries)
            amount = float(match.group(1))
            if not math.isfinite(amount):
                return absent("NONFINITE_MEASUREMENT", entries)
            parsed.append((name, amount))
        if len({amount for _, amount in parsed}) != 1:
            return absent("CONFLICTING_MEASUREMENTS", entries)
        name, amount = parsed[0]
        unit = "kWh/year"
    else:
        if len(entries) != 1:
            return absent("MISSING_OR_MULTIPLE_MEASUREMENTS", entries)
        source = entries[0]
        name, value = source.get("name"), source.get("value")
        if not isinstance(name, str) or not isinstance(value, str):
            return absent("UNSUPPORTED_MEASUREMENT_ENCODING", entries)
        if name != "Total Capacity (cu. ft.)":
            return absent("UNSUPPORTED_CAPACITY_FIELD_UNIT", entries)
        match = re.fullmatch(number + r"(?:\s*cu\.?\s*ft\.?)?", value.strip(), re.I)
        unit = "cu ft"
        if match is None:
            return absent("AMBIGUOUS_NUMBER_OR_UNIT", entries)
        amount = float(match.group(1))
        if not math.isfinite(amount):
            return absent("NONFINITE_MEASUREMENT", entries)
    raw_value = "; ".join(f"{source['name']}: {source['value']}" for source in entries)
    return observed({"amount": amount, "unit": unit, "raw": raw_value}, entries)


def normalize_pdp(
    specs: dict[str, Any],
    plp_flags: list[Any],
    structured_fields: list[dict[str, Any]],
    *,
    allow_refrigerator_energy_rows: bool = False,
) -> dict[str, Any]:
    channels = {
        "pdp_annual_energy_kwh": measurement(
            specs["energy_consumption_raw"],
            "annual_energy",
            allow_refrigerator_energy_rows=allow_refrigerator_energy_rows,
        ),
        "pdp_capacity": measurement(specs["capacity_raw"], "capacity"),
        "plp_energy_star_claim": claim(plp_flags),
        "pdp_structured_energy_star_claim": claim([f.get("value") for f in structured_fields]),
        "pdp_spec_energy_star_claim": claim(
            [f.get("value") for f in specs["energy_star_spec_claim_raw"]]
        ),
    }
    return {
        "normalization_version": "pdp-source-encoding-1",
        "scope": "source values only; not EPA certification or FTC comparison",
        "exact_sku": specs["exact_sku"],
        "channels": channels,
        "observations": {name: entry["observation"] for name, entry in channels.items()},
    }

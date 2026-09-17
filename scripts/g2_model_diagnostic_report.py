"""Apply the approved positional diagnostic to saved review observations only."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_epa_wildcard_capture import SOURCES, positional_diagnostic  # noqa: E402
from g2_samsung_suffix import normalize_terminal_aa  # noqa: E402


def observe_us_market(markets, *, source_status: str) -> str:
    """Observe a literal comma-delimited EPA market; not certification status."""
    if source_status != "PASS":
        raise ValueError("EPA source capture failed; market observation unavailable")
    if not isinstance(markets, str) or not markets.strip():
        return "NOT_EVALUATED"
    tokens = [token.strip() for token in markets.split(",")]
    if any(not token for token in tokens):
        return "NOT_EVALUATED"
    return "OBSERVED_US_MARKET" if "United States" in tokens else "NOT_EVALUATED"


def build_report() -> dict:
    review = json.loads(
        (ROOT / "docs/evidence/g2-capacity-model-review.json").read_text(encoding="utf-8")
    )
    metadata_hash = "6fca2122b9db18d3ca53121b397606157c3de70d0237c1bee546a4ba10148b11"
    epa = json.loads(
        (ROOT / "tests/fixtures/g2-epa-wildcard/api-record.json").read_text(encoding="utf-8")
    )
    source_row = epa["projection"]
    if source_row["brand_name"] != "Samsung" or not source_row["model_number"]:
        raise ValueError("EPA source fixture identity invalid")
    pattern = source_row["model_number"]
    records = []
    for item in review["records"]:
        for sku in item["exact_skus"]:
            normalized = normalize_terminal_aa(sku)
            diagnostic = positional_diagnostic(
                pattern,
                normalized["normalized_identifier"],
                dataset_id="p5st-her9",
                metadata_sha256=metadata_hash,
            )
            inclusion = {
                "POSITIONAL_COMPATIBLE_DIAGNOSTIC_ONLY": "INCLUDED",
                "POSITIONAL_INCOMPATIBLE_DIAGNOSTIC_ONLY": "NOT_INCLUDED",
                "WITHHELD_LENGTH_MISMATCH": "NOT_INCLUDED",
            }.get(diagnostic["diagnostic"], "UNKNOWN")
            records.append(
                {
                    "exact_sku": sku,
                    "terminal_suffix_normalization": normalized,
                    "pdf_sha256": item["pdf_sha256"],
                    "label_model_raw": item["model_token_raw"],
                    "epa_pattern_raw": pattern,
                    "epa_source_body_sha256": epa["body_sha256"],
                    "epa_source_url": SOURCES[epa["source"]],
                    "epa_pd_id": source_row["pd_id"],
                    "model_pattern_inclusion": inclusion,
                    "current_certification_state": "NOT_EVALUATED",
                    "markets_raw": source_row["markets"],
                    "date_qualified_raw": source_row.get("date_qualified"),
                    "us_applicability_state": observe_us_market(
                        source_row.get("markets"), source_status="PASS"
                    ),
                    "us_market_observation_scope": "EPA_ROW_ONLY",
                    "assessment": "NOT_EVALUATED",
                    "full_sku_diagnostic": positional_diagnostic(
                        pattern, sku, dataset_id="p5st-her9", metadata_sha256=metadata_hash
                    ),
                    "normalized_identifier_diagnostic": diagnostic,
                }
            )
    return {
        "contract": "G2_MODEL_PATTERN_INCLUSION_OBSERVATION_ONLY_V3",
        "scope": "one saved EPA row against review corpus; not exhaustive candidate search",
        "identity_state": "NOT_EVALUATED",
        "correction_state": "NOT_APPLIED",
        "records": records,
    }


if __name__ == "__main__":
    out = ROOT / "runtime/g2-model-diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(build_report(), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "records": len(build_report()["records"])}))

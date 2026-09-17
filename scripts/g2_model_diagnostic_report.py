"""Apply the approved positional diagnostic to saved review observations only."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_epa_wildcard_capture import positional_diagnostic


def build_report() -> dict:
    review = json.loads(
        (ROOT / "docs/evidence/g2-capacity-model-review.json").read_text(encoding="utf-8")
    )
    metadata_hash = "6fca2122b9db18d3ca53121b397606157c3de70d0237c1bee546a4ba10148b11"
    records = []
    for item in review["records"]:
        for sku in item["exact_skus"]:
            records.append(
                {
                    "exact_sku": sku,
                    "pdf_sha256": item["pdf_sha256"],
                    "label_model_raw": item["model_token_raw"],
                    "epa_pattern_raw": "RF23D*9600**",
                    "diagnostic": positional_diagnostic(
                        "RF23D*9600**", sku, dataset_id="p5st-her9", metadata_sha256=metadata_hash
                    ),
                }
            )
    return {
        "contract": "G2_MODEL_DIAGNOSTIC_SOURCE_OBSERVATION_ONLY_V1",
        "identity_state": "NOT_EVALUATED",
        "correction_state": "NOT_APPLIED",
        "records": records,
    }


if __name__ == "__main__":
    out = ROOT / "runtime/g2-model-diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(build_report(), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "records": len(build_report()["records"])}))

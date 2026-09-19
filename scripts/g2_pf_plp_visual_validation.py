"""Calibrate the exact-SKU PF flag against rendered PLP logo observations.

This is an observational check only.  It does not make the PF field a
publication finding, and it does not emit an audit assessment.
"""

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from g2_energy_star_publication_points import ABSENT, PRESENT, UNKNOWN, plp_logo_point


CONTRACT = "G2_PF_PLP_RENDERED_CARD_CALIBRATION_V1"


def calibrate(pf_records: list[dict[str, Any]], cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Return descriptive agreement counts for exact cards that were rendered.

    A missing PLP card is deliberately excluded: it is not visual absence.
    Only literal Y and N are compared; any other raw PF value is retained but
    withheld from the comparison.
    """
    flags: dict[str, Any] = {}
    for record in pf_records:
        sku = record.get("exact_sku")
        if not isinstance(sku, str) or not sku:
            raise ValueError("PF record has no exact SKU")
        flag = record.get("plp_energy_star_claim_raw")
        if sku in flags and flags[sku] != flag:
            raise ValueError("PF exact SKU has conflicting Energy Star flags")
        flags[sku] = flag

    card_skus = [card.get("sku") for card in cards]
    if any(not isinstance(sku, str) or not sku for sku in card_skus):
        raise ValueError("Rendered PLP card has no exact SKU")
    if len(card_skus) != len(set(card_skus)):
        raise ValueError("Rendered PLP cards have duplicate exact SKUs")
    unknown_cards = sorted(set(card_skus) - set(flags))
    if unknown_cards:
        raise ValueError("Rendered PLP card is absent from current PF population")
    for card in cards:
        sku = card["sku"]
        if card.get("card_scope_contract") != "PLP_EXACT_LIST_ITEM_V2":
            raise ValueError("Rendered PLP card lacks exact-card scope contract")
        if card.get("exact_sku_anchor_count") != 1 or card.get("exact_sku_anchor_values") != [sku]:
            raise ValueError("Rendered PLP card has ambiguous exact-SKU ownership")

    records = []
    counts = Counter()
    for sku in sorted(card_skus):
        raw_flag = flags[sku]
        visual = plp_logo_point(cards, sku)
        result = "WITHHELD"
        if raw_flag not in ("Y", "N"):
            counts["raw_flag_unrecognized"] += 1
        elif visual["state"] == UNKNOWN:
            counts["visual_unknown"] += 1
        else:
            counts["comparable"] += 1
            expected = PRESENT if raw_flag == "Y" else ABSENT
            result = "AGREEMENT" if visual["state"] == expected else "DISAGREEMENT"
            counts[result.lower()] += 1
            counts[f"pf_{raw_flag.lower()}_comparable"] += 1
        records.append({
            "exact_sku": sku,
            "pf_energy_star_flag_raw": raw_flag,
            "plp_logo_visual": visual,
            "comparison_result": result,
        })

    comparable = counts["comparable"]
    if not comparable:
        conclusion = "INSUFFICIENT_COMPARABLE_EVIDENCE"
    elif counts["disagreement"]:
        conclusion = "OBSERVED_DISAGREEMENTS"
    elif not counts["pf_n_comparable"]:
        conclusion = "OBSERVED_POSITIVE_ONLY_AGREEMENT"
    else:
        conclusion = "OBSERVED_AGREEMENT"
    return {
        "contract": CONTRACT,
        "scope": "Current Samsung refrigerator rendered PLP cards and their own PF exact-SKU flags; no variant sharing and no audit assessment",
        "calibration_conclusion": conclusion,
        "comparison_counts": {
            "pf_population_exact_skus": len(flags),
            "rendered_exact_cards": len(card_skus),
            "population_not_rendered": len(set(flags) - set(card_skus)),
            "comparable": comparable,
            "agreement": counts["agreement"],
            "disagreement": counts["disagreement"],
            "pf_y_comparable": counts["pf_y_comparable"],
            "pf_n_comparable": counts["pf_n_comparable"],
            "visual_unknown": counts["visual_unknown"],
            "raw_flag_unrecognized": counts["raw_flag_unrecognized"],
        },
        "records": records,
    }


def load_pf_records(source_dir: Path) -> list[dict[str, Any]]:
    recon = json.loads((source_dir / "recon.json").read_text(encoding="utf-8"))
    if recon.get("status") != "PASS":
        raise ValueError("Source recon did not pass")
    fixtures = [item["fixture"] for item in recon.get("observations", []) if item.get("fixture")]
    if not fixtures:
        raise ValueError("Source recon has no PF fixtures")
    records = []
    for fixture in fixtures:
        page = json.loads((source_dir / fixture).read_text(encoding="utf-8"))
        for group in page.get("searchResults", []):
            for variant in group.get("groupedProductList", []):
                records.append({
                    "exact_sku": variant.get("modelCode"),
                    "plp_energy_star_claim_raw": variant.get("energyStarFlg"),
                })
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=Path("runtime/source-recon/refrigerator"))
    parser.add_argument("--output", type=Path, default=Path("runtime/g2-pf-plp-visual-validation/plp-visual-calibration.json"))
    parser.add_argument("--collect", action="store_true", help="Run the current source recon before calibrating")
    args = parser.parse_args()
    if args.collect:
        subprocess.run([sys.executable, "scripts/source_recon.py", "--family", "refrigerator"], check=True)
    cards_file = args.source_dir / "plp-claim-observation.json"
    cards = json.loads(cards_file.read_text(encoding="utf-8")).get("cards")
    if not isinstance(cards, list):
        raise ValueError("Rendered PLP card observation is missing")
    report = calibrate(load_pf_records(args.source_dir), cards)
    report.update({"captured_at": datetime.now(timezone.utc).isoformat(), "status": "PASS"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["comparison_counts"], sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

"""Profile G2 EnergyGuide source and review-binding coverage from an artifact ZIP."""

from collections import Counter, defaultdict
import argparse
import json
from pathlib import Path
import re
import zipfile


CONTRACT = "G2_ENERGYGUIDE_QUALITY_PROFILE_V1"


def _one_json(archive: zipfile.ZipFile, pattern: str) -> dict:
    names = [name for name in archive.namelist() if re.search(pattern, name)]
    if len(names) != 1:
        raise ValueError(f"Artifact must contain exactly one {pattern}")
    return json.loads(archive.read(names[0]))


def _value(fact: dict, name: str):
    observation = fact.get("observations", {}).get(name, {})
    return observation.get("value") if observation.get("state") == "VALUE" else None


def build_quality_profile(archive_path: Path, *, github_run_id: str | None = None) -> dict:
    with zipfile.ZipFile(archive_path) as archive:
        checkpoint = _one_json(archive, r"/checkpoint\.json$")
        bundle = _one_json(archive, r"/bundle\.json$")

    if checkpoint.get("status") != "PASS":
        raise ValueError("G2 source checkpoint is not successful")
    manifest = bundle.get("manifest", {})
    if checkpoint.get("run_id") != manifest.get("run_id"):
        raise ValueError("G2 checkpoint and bundle run IDs differ")
    products = bundle.get("products")
    if not isinstance(products, list) or not products:
        raise ValueError("G2 product population is unavailable")
    product_skus = {product.get("exact_sku") for product in products}
    if None in product_skus or len(product_skus) != len(products):
        raise ValueError("G2 product exact SKU grain is invalid")
    facts = [fact for fact in bundle.get("facts", []) if fact.get("kind") == "ENERGYGUIDE"]
    fact_skus = [fact.get("exact_sku") for fact in facts]
    if len(facts) != len(product_skus) or set(fact_skus) != product_skus:
        raise ValueError("EnergyGuide fact coverage differs from product population")

    annual_summary = checkpoint.get("label_selection_summary", {})
    capacity_summary = checkpoint.get("capacity_selection_summary", {})
    annual_records = annual_summary.get("records")
    capacity_records = capacity_summary.get("records")
    if not isinstance(annual_records, list) or not isinstance(capacity_records, list):
        raise ValueError("Label review summaries are unavailable")
    if {row.get("exact_sku") for row in annual_records} != product_skus:
        raise ValueError("Annual-energy review coverage differs from product population")
    if {row.get("exact_sku") for row in capacity_records} != product_skus:
        raise ValueError("Capacity review coverage differs from product population")

    annual_by_sku = {row["exact_sku"]: row for row in annual_records}
    capacity_by_sku = {row["exact_sku"]: row for row in capacity_records}
    pdf_groups: dict[str, list[str]] = defaultdict(list)
    engines = Counter()
    fallbacks = Counter()
    model_states = Counter()
    rows = []
    for fact in sorted(facts, key=lambda item: item["exact_sku"]):
        sku = fact["exact_sku"]
        digest = _value(fact, "document_sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("EnergyGuide PDF hash is missing or invalid")
        engine = _value(fact, "extraction_engine")
        fallback = _value(fact, "fallback_reason") or "NONE"
        model_state = fact["observations"]["label_model_raw"]["state"]
        engines[str(engine)] += 1
        fallbacks[str(fallback)] += 1
        model_states[str(model_state)] += 1
        pdf_groups[digest].append(sku)
        annual = annual_by_sku[sku]
        capacity = capacity_by_sku[sku]
        rows.append({
            "exact_sku": sku,
            "pdf_sha256": digest,
            "extraction_engine": engine,
            "fallback_reason": fallback,
            "raw_model_state": model_state,
            "raw_model_value": _value(fact, "label_model_raw"),
            "annual_energy_state": annual["annual_energy_observation"]["state"],
            "annual_energy_reason": annual["selection_reason"],
            "capacity_state": capacity["capacity_observation"]["state"],
            "capacity_reason": capacity["selection_reason"],
        })

    annual_value = sum(row["annual_energy_state"] == "VALUE" for row in rows)
    capacity_value = sum(row["capacity_state"] == "VALUE" for row in rows)
    annual_reviewed_hashes = {
        row["pdf_sha256"] for row in rows if row["annual_energy_state"] == "VALUE"
    }
    capacity_reviewed_hashes = {
        row["pdf_sha256"] for row in rows if row["capacity_state"] == "VALUE"
    }
    groups = [
        {
            "pdf_sha256": digest,
            "exact_skus": sorted(skus),
            "exact_sku_count": len(skus),
            "annual_energy_value_bound": digest in annual_reviewed_hashes,
            "capacity_value_bound": digest in capacity_reviewed_hashes,
        }
        for digest, skus in sorted(pdf_groups.items())
    ]
    population = len(product_skus)
    unique_pdfs = len(groups)
    return {
        "contract": CONTRACT,
        "status": "SOURCE_COMPLETE_REVIEW_BINDING_INCOMPLETE",
        "source": {
            "github_run_id": github_run_id,
            "execution_run_id": manifest["run_id"],
            "git_sha": manifest.get("git_sha"),
            "artifact_zip": archive_path.name,
        },
        "grain": {
            "product_key": "exact_sku",
            "review_reuse_key": "pdf_sha256",
        },
        "counts": {
            "population_exact_skus": population,
            "energyguide_facts": len(facts),
            "source_pdf_parsed": sum(_value(fact, "document_status") == "SOURCE_PDF_PARSED" for fact in facts),
            "unique_pdf_hashes": unique_pdfs,
            "shared_pdf_hash_groups": sum(group["exact_sku_count"] > 1 for group in groups),
            "raw_model_values": model_states["VALUE"],
            "raw_model_not_observed": population - model_states["VALUE"],
            "annual_energy_values": annual_value,
            "annual_energy_not_observed": population - annual_value,
            "capacity_values": capacity_value,
            "capacity_not_observed": population - capacity_value,
            "annual_energy_reviewed_pdf_hashes": len(annual_reviewed_hashes),
            "annual_energy_unreviewed_pdf_hashes": unique_pdfs - len(annual_reviewed_hashes),
            "capacity_reviewed_pdf_hashes": len(capacity_reviewed_hashes),
            "capacity_unreviewed_pdf_hashes": unique_pdfs - len(capacity_reviewed_hashes),
        },
        "rates": {
            "source_fact_coverage": len(facts) / population,
            "annual_energy_value_coverage": annual_value / population,
            "capacity_value_coverage": capacity_value / population,
        },
        "extraction_engines": dict(sorted(engines.items())),
        "fallback_reasons": dict(sorted(fallbacks.items())),
        "risks": [
            {
                "severity": "HIGH",
                "finding": "Annual-energy review binding is incomplete for downstream comparison",
                "affected_exact_skus": population - annual_value,
                "affected_pdf_hashes": unique_pdfs - len(annual_reviewed_hashes),
                "control": "Keep annual energy NOT_OBSERVED until byte-identical PDF/panel review is recorded",
            },
            {
                "severity": "HIGH",
                "finding": "Capacity review binding is incomplete for OCR corroboration",
                "affected_exact_skus": population - capacity_value,
                "affected_pdf_hashes": unique_pdfs - len(capacity_reviewed_hashes),
                "control": "Keep capacity NOT_OBSERVED until byte-identical PDF/panel review is recorded",
            },
            {
                "severity": "MEDIUM",
                "finding": "Most source labels require OCR rather than embedded-text extraction",
                "affected_exact_skus": engines.get("RapidOCR", 0),
                "control": "Retain raw OCR, coordinates, PDF hash and reviewed panel evidence",
            },
            {
                "severity": "MEDIUM",
                "finding": "Some labels contain missing or ambiguous raw model candidates",
                "affected_exact_skus": population - model_states["VALUE"],
                "control": "Preserve every raw model candidate and withhold model identity until its pattern rule is reviewed",
            },
        ],
        "pdf_groups": groups,
        "records": rows,
        "overall_product_compliance": "NOT_EVALUATED",
    }


def render_markdown(profile: dict) -> str:
    counts = profile["counts"]
    engines = profile["extraction_engines"]
    return "\n".join([
        "# G2 refrigerator EnergyGuide quality profile",
        "",
        f"Source GitHub run: `{profile['source']['github_run_id']}`",
        "",
        "| Exact SKUs | Parsed source PDFs | Unique PDF hashes | RapidOCR | Embedded text |",
        "|---:|---:|---:|---:|---:|",
        f"| {counts['population_exact_skus']} | {counts['source_pdf_parsed']} | {counts['unique_pdf_hashes']} | {engines.get('RapidOCR', 0)} | {engines.get('PyMuPDF', 0)} |",
        "",
        "| Review-bound field | VALUE SKUs | NOT_OBSERVED SKUs | Reviewed PDF hashes | Unreviewed PDF hashes |",
        "|---|---:|---:|---:|---:|",
        f"| Annual energy | {counts['annual_energy_values']} | {counts['annual_energy_not_observed']} | {counts['annual_energy_reviewed_pdf_hashes']} | {counts['annual_energy_unreviewed_pdf_hashes']} |",
        f"| Capacity | {counts['capacity_values']} | {counts['capacity_not_observed']} | {counts['capacity_reviewed_pdf_hashes']} | {counts['capacity_unreviewed_pdf_hashes']} |",
        "",
        "Source collection is complete. Review binding is incomplete, so missing reviewed values remain NOT_OBSERVED and overall product compliance remains NOT_EVALUATED.",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", type=Path)
    parser.add_argument("--github-run-id")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    profile = build_quality_profile(args.artifact_zip, github_run_id=args.github_run_id)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(profile), encoding="utf-8")
    if not args.json_output and not args.markdown_output:
        print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    main()

"""Profile G2 EnergyGuide source and review-binding coverage from an artifact ZIP."""

from collections import Counter, defaultdict
import argparse
import hashlib
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


def build_quality_profile(
    archive_path: Path,
    *,
    github_run_id: str | None = None,
    selection_replay: dict | None = None,
) -> dict:
    with zipfile.ZipFile(archive_path) as archive:
        checkpoint = _one_json(archive, r"/checkpoint\.json$")
        bundle = _one_json(archive, r"/bundle\.json$")
        candidate_entries = [
            name for name in archive.namelist()
            if name.endswith("energyguide-field-candidates.json")
        ]
        candidates_by_hash: dict[str, list[tuple[str, dict]]] = defaultdict(list)
        for name in candidate_entries:
            candidate = json.loads(archive.read(name))
            digest = candidate.get("pdf_sha256")
            if not isinstance(digest, str):
                raise ValueError("EnergyGuide candidate PDF hash is missing")
            candidates_by_hash[digest].append((name, candidate))
        pdf_entries_by_hash: dict[str, list[str]] = defaultdict(list)
        for name in archive.namelist():
            if "energyguide" not in name.lower() or not name.lower().endswith(".pdf"):
                continue
            digest = hashlib.sha256(archive.read(name)).hexdigest()
            pdf_entries_by_hash[digest].append(name)

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

    if selection_replay is not None:
        if selection_replay.get("contract") != "G2_LABEL_ANNOTATION_REPLAY_V1" or selection_replay.get("status") != "PASS":
            raise ValueError("Selection replay contract is invalid")
        if selection_replay.get("source", {}).get("execution_run_id") != manifest.get("run_id"):
            raise ValueError("Selection replay source run differs from artifact")
    selection_source = selection_replay or checkpoint
    annual_summary = selection_source.get("label_selection_summary", {})
    capacity_summary = selection_source.get("capacity_selection_summary", {})
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
    annual_value_hashes = {
        row["pdf_sha256"] for row in rows if row["annual_energy_state"] == "VALUE"
    }
    capacity_value_hashes = {
        row["pdf_sha256"] for row in rows if row["capacity_state"] == "VALUE"
    }
    groups = [
        {
            "pdf_sha256": digest,
            "exact_skus": sorted(skus),
            "exact_sku_count": len(skus),
            "annual_energy_value_bound": digest in annual_value_hashes,
            "capacity_value_bound": digest in capacity_value_hashes,
            "source_pdf_entries": sorted(pdf_entries_by_hash.get(digest, [])),
            "source_candidate_entries": sorted(
                name for name, _candidate in candidates_by_hash.get(digest, [])
            ),
            "candidates": _candidate_projection(candidates_by_hash.get(digest, [])),
        }
        for digest, skus in sorted(pdf_groups.items())
    ]
    if any(not group["source_pdf_entries"] or not group["source_candidate_entries"] for group in groups):
        raise ValueError("EnergyGuide review source files are missing from artifact")
    population = len(product_skus)
    unique_pdfs = len(groups)
    annual_missing = population - annual_value
    capacity_missing = population - capacity_value
    risks = []
    if annual_missing:
        risks.append({
            "severity": "HIGH",
            "finding": "Annual-energy source selection is incomplete for downstream comparison",
            "affected_exact_skus": annual_missing,
            "affected_pdf_hashes": unique_pdfs - len(annual_value_hashes),
            "control": "Keep annual energy NOT_OBSERVED until the strict rule or a byte-bound review selects it",
        })
    if capacity_missing:
        risks.append({
            "severity": "HIGH",
            "finding": "Capacity source selection is incomplete for downstream comparison",
            "affected_exact_skus": capacity_missing,
            "affected_pdf_hashes": unique_pdfs - len(capacity_value_hashes),
            "control": "Keep capacity NOT_OBSERVED until the strict rule or a byte-bound review selects it",
        })
    risks.extend([
        {
            "severity": "MEDIUM",
            "finding": "Most source labels require OCR rather than embedded-text extraction",
            "affected_exact_skus": engines.get("RapidOCR", 0),
            "control": "Retain raw OCR, coordinates, PDF hash and reviewed exceptions",
        },
        {
            "severity": "MEDIUM",
            "finding": "Some labels contain missing or ambiguous raw model candidates",
            "affected_exact_skus": population - model_states["VALUE"],
            "control": "Preserve every raw model candidate and withhold model identity until its pattern rule is reviewed",
        },
    ])
    return {
        "contract": CONTRACT,
        "status": (
            "SOURCE_AND_NUMERIC_SELECTION_COMPLETE"
            if not annual_missing and not capacity_missing
            else "SOURCE_COMPLETE_NUMERIC_SELECTION_INCOMPLETE"
        ),
        "source": {
            "github_run_id": github_run_id,
            "execution_run_id": manifest["run_id"],
            "git_sha": manifest.get("git_sha"),
            "artifact_zip": archive_path.name,
            "selection_binding": "CURRENT_ANNOTATION_REPLAY" if selection_replay else "ARTIFACT_CHECKPOINT",
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
            "annual_energy_value_pdf_hashes": len(annual_value_hashes),
            "annual_energy_not_observed_pdf_hashes": unique_pdfs - len(annual_value_hashes),
            "capacity_value_pdf_hashes": len(capacity_value_hashes),
            "capacity_not_observed_pdf_hashes": unique_pdfs - len(capacity_value_hashes),
        },
        "rates": {
            "source_fact_coverage": len(facts) / population,
            "annual_energy_value_coverage": annual_value / population,
            "capacity_value_coverage": capacity_value / population,
        },
        "extraction_engines": dict(sorted(engines.items())),
        "fallback_reasons": dict(sorted(fallbacks.items())),
        "risks": risks,
        "pdf_groups": groups,
        "review_queue": [
            {
                "priority": (
                    "MODEL_AMBIGUOUS"
                    if len(group["candidates"]["model_values_raw"]) != 1
                    else "ANNUAL_AND_CAPACITY"
                    if not group["annual_energy_value_bound"] and not group["capacity_value_bound"]
                    else "ANNUAL_ONLY"
                    if not group["annual_energy_value_bound"]
                    else "CAPACITY_ONLY"
                ),
                **group,
            }
            for group in groups
            if not group["annual_energy_value_bound"] or not group["capacity_value_bound"]
               or len(group["candidates"]["model_values_raw"]) != 1
        ],
        "records": rows,
        "overall_product_compliance": "NOT_EVALUATED",
    }


def _candidate_projection(entries: list[tuple[str, dict]]) -> dict:
    if not entries:
        return {"model_values_raw": [], "annual_energy_candidates": [], "capacity_values_raw": []}
    projections = []
    for _name, candidate in entries:
        projection = {
            "model_values_raw": [
                row.get("value_raw") for row in candidate.get("model_candidates_raw", [])
            ],
            "annual_energy_candidates": [
                {
                    "value_raw": row.get("value_raw"),
                    "unit_raw": row.get("unit_raw"),
                    "role": row.get("role"),
                }
                for row in candidate.get("energy_candidates_raw", [])
            ],
            "capacity_values_raw": [
                row.get("value_raw") for row in candidate.get("capacity_candidates_raw", [])
            ],
        }
        projections.append(projection)
    canonical = {json.dumps(item, sort_keys=True) for item in projections}
    if len(canonical) != 1:
        raise ValueError("Byte-identical EnergyGuide PDFs produced different candidate projections")
    return projections[0]


def render_markdown(profile: dict) -> str:
    counts = profile["counts"]
    engines = profile["extraction_engines"]
    lines = [
        "# G2 refrigerator EnergyGuide quality profile",
        "",
        f"Source GitHub run: `{profile['source']['github_run_id']}`",
        "",
        "| Exact SKUs | Parsed source PDFs | Unique PDF hashes | RapidOCR | Embedded text |",
        "|---:|---:|---:|---:|---:|",
        f"| {counts['population_exact_skus']} | {counts['source_pdf_parsed']} | {counts['unique_pdf_hashes']} | {engines.get('RapidOCR', 0)} | {engines.get('PyMuPDF', 0)} |",
        "",
        "| Selected field | VALUE SKUs | NOT_OBSERVED SKUs | VALUE PDF hashes | NOT_OBSERVED PDF hashes |",
        "|---|---:|---:|---:|---:|",
        f"| Annual energy | {counts['annual_energy_values']} | {counts['annual_energy_not_observed']} | {counts['annual_energy_value_pdf_hashes']} | {counts['annual_energy_not_observed_pdf_hashes']} |",
        f"| Capacity | {counts['capacity_values']} | {counts['capacity_not_observed']} | {counts['capacity_value_pdf_hashes']} | {counts['capacity_not_observed_pdf_hashes']} |",
        "",
        (
            "Source collection and numeric field selection are complete. Overall product compliance remains NOT_EVALUATED until comparison rules run."
            if profile["status"] == "SOURCE_AND_NUMERIC_SELECTION_COMPLETE"
            else "Source collection is complete. Missing numeric selections remain NOT_OBSERVED and overall product compliance remains NOT_EVALUATED."
        ),
        "",
        "## PDF-hash review queue",
        "",
        "One row is one byte-distinct PDF. Exact SKUs remain separate members of the row.",
        "",
        "| Priority | PDF SHA-256 | Exact SKUs | Model candidates | Annual-energy candidates | Capacity candidates |",
        "|---|---|---|---|---|---|",
    ]
    for item in profile["review_queue"]:
        candidates = item["candidates"]
        energy = ", ".join(
            f"{row.get('value_raw')} {row.get('unit_raw')}" for row in candidates["annual_energy_candidates"]
        )
        lines.append(
            "| {priority} | `{digest}` | {skus} | {models} | {energy} | {capacity} |".format(
                priority=item["priority"],
                digest=item["pdf_sha256"],
                skus=_markdown_cell(", ".join(item["exact_skus"])),
                models=_markdown_cell(", ".join(str(value) for value in candidates["model_values_raw"])),
                energy=_markdown_cell(energy),
                capacity=_markdown_cell(", ".join(str(value) for value in candidates["capacity_values_raw"])),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>") or "—"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", type=Path)
    parser.add_argument("--github-run-id")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--selection-replay", type=Path)
    args = parser.parse_args()
    replay_document = (
        json.loads(args.selection_replay.read_text(encoding="utf-8"))
        if args.selection_replay else None
    )
    profile = build_quality_profile(
        args.artifact_zip,
        github_run_id=args.github_run_id,
        selection_replay=replay_document,
    )
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

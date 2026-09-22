"""Summarize TV label OCR/model/energy/capacity candidates without selecting or assessing."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re


CONTRACT = "G3_TV_ENERGYGUIDE_RAW_CANDIDATE_REVIEW_V1"


def read_json(path):
    return json.loads(Path(path).read_bytes())


def review(observation_root, observation_run_id, output):
    root = Path(observation_root).resolve()
    summary = read_json(root / "observation-summary.json")
    if summary.get("status") != "PASS" or str(summary.get("observation_run_id")) != str(observation_run_id):
        raise ValueError("TV observation artifact is not the requested successful run")
    source = summary.get("source", {})
    sku_docs = source.get("sku_documents")
    if not isinstance(sku_docs, list) or len(sku_docs) != source.get("sku_document_count"):
        raise ValueError("TV SKU-document provenance count is invalid")
    sku_coverage = source.get("sku_document_coverage")
    if not isinstance(sku_coverage, list) or len(sku_coverage) != source.get("sku_population_count"):
        raise ValueError("TV per-SKU Support-document coverage is invalid")
    coverage_by_sku = {row.get("exact_sku"): row.get("support_document_count") for row in sku_coverage
                       if isinstance(row, dict) and isinstance(row.get("exact_sku"), str)}
    linked_counts = Counter(row.get("exact_sku") for row in sku_docs)
    if (len(coverage_by_sku) != len(sku_coverage)
            or not set(linked_counts) <= set(coverage_by_sku)
            or any(coverage_by_sku[sku] != linked_counts.get(sku, 0) for sku in coverage_by_sku)):
        raise ValueError("TV per-SKU document counts disagree with exact-SKU PDF links")
    skus_without_documents = [row["exact_sku"] for row in sku_coverage
                              if row.get("state") == "NO_SUPPORT_DOCUMENT_DECLARED"]
    skus_without_review_document = [row["exact_sku"] for row in sku_coverage
                                    if row.get("state") in ("NO_SUPPORT_DOCUMENT_DECLARED", "PDP_NOT_VERIFIED")]
    by_hash = {}
    for link in sku_docs:
        digest = link.get("pdf_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("TV SKU-document PDF hash is invalid")
        by_hash.setdefault(digest, []).append(link)
    entries, table = [], []
    for item in summary.get("observations", []):
        digest = item.get("pdf_sha256")
        if item.get("status") != "OBSERVED" or digest not in by_hash:
            raise ValueError("TV observed PDF is not linked to an exact-SKU source document")
        relative = item.get("observation_path")
        if not isinstance(relative, str):
            raise ValueError("TV observation path is missing")
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("TV observation path is missing or unsafe")
        observation = read_json(path)
        if observation.get("pdf_sha256") != digest:
            raise ValueError("TV observation PDF hash does not match its source index")
        model_rows, energy_rows, capacity_rows = [], [], []
        headings = observation.get("label_heading_observations", {})
        for page in observation.get("pages", []):
            layers = [("PRIMARY_TEXT", page.get("fields_raw")),
                      ("OCR_COMPLEMENT", (page.get("ocr_complement_raw") or {}).get("fields_raw"))]
            for layer, fields in layers:
                fields = fields or {}
                for candidate in fields.get("model_candidates_raw", []):
                    model_rows.append({"page": page.get("page"), "evidence_layer": layer, **candidate})
                for candidate in fields.get("energy_candidates_raw", []):
                    energy_rows.append({"page": page.get("page"), "evidence_layer": layer, **candidate})
                for candidate in fields.get("capacity_candidates_raw", []):
                    capacity_rows.append({"page": page.get("page"), "evidence_layer": layer, **candidate})
        model_values = sorted({row.get("value_raw") for row in model_rows if row.get("value_raw")})
        declared_models = sorted({row.get("value_raw") for row in model_rows
                                  if row.get("value_raw") and re.search(r"\bmodels?\b", row.get("context_raw", ""), re.I)})
        annual_rows = [row for row in energy_rows if row.get("role") == "ANNUAL_CAPTION_CONTEXT"]
        energy_values = sorted({row.get("value_raw") for row in annual_rows if row.get("value_raw")})
        capacity_values = sorted({row.get("value_raw") for row in capacity_rows
                                  if row.get("value_raw") and re.search(r"capacity\s*\(\s*tub\s+volume\s*\)", row.get("value_raw", ""), re.I)})
        us_count = len(headings.get("us_energyguide_heading_candidates", []))
        ca_count = len(headings.get("canada_energuide_heading_candidates", []))
        flags = []
        if len(declared_models) != 1:
            flags.append("PRINTED_MODEL_DECLARATION_CANDIDATE_COUNT_" + str(len(declared_models)))
        if any("*" in value or "?" in value for value in declared_models):
            flags.append("WILDCARD_MODEL_TOKEN_PRESENT")
        if len(energy_values) != 1:
            flags.append("ANNUAL_ENERGY_CANDIDATE_COUNT_" + str(len(energy_values)))
        if us_count == 0:
            flags.append("US_ENERGYGUIDE_HEADING_NOT_OBSERVED")
        if ca_count:
            flags.append("CANADIAN_ENERGUIDE_HEADING_ALSO_OBSERVED")
        row = {"pdf_sha256": digest, "source_urls": observation.get("source_urls", []),
               "exact_skus": sorted({link["exact_sku"] for link in by_hash[digest]}),
               "sku_document_count": len(by_hash[digest]), "page_count": observation.get("page_count"),
               "text_engines": sorted({span.get("engine") for page in observation.get("pages", [])
                                        for span in page.get("spans_raw", []) if span.get("engine")}),
               "model_candidates_raw": model_rows, "annual_energy_candidates_raw": energy_rows,
               "capacity_candidates_raw": capacity_rows,
               "us_heading_candidates_raw": headings.get("us_energyguide_heading_candidates", []),
               "canada_heading_candidates_raw": headings.get("canada_energuide_heading_candidates", []),
               "review_flags": flags, "selection": "NOT_EVALUATED", "matching": "NOT_EVALUATED",
               "assessment": "NOT_EVALUATED"}
        entries.append(row)
        table.append({"pdf_sha256": digest, "exact_skus": row["exact_skus"],
                      "models_raw": declared_models, "all_model_like_tokens_raw": model_values,
                      "annual_kwh_raw": energy_values,
                      "annual_evidence_raw": [{"value_raw": entry.get("value_raw"),
                                               "evidence_layer": entry.get("evidence_layer"),
                                               "role": entry.get("role")}
                                              for entry in annual_rows],
                      "model_evidence_raw": [{"value_raw": entry.get("value_raw"),
                                              "evidence_layer": entry.get("evidence_layer")}
                                             for entry in model_rows if entry.get("value_raw") in declared_models],
                      "other_energy_roles_raw": sorted({str(x.get("role")) for x in energy_rows if x not in annual_rows}),
                      "capacity_raw": capacity_values, "us_heading_count": us_count,
                      "canada_heading_count": ca_count, "review_flags": flags})
    if len(entries) != summary.get("observed_pdf_count") or len(entries) != len(by_hash):
        raise ValueError("Observed PDF count does not match hash-bound source population")
    report = {"contract": CONTRACT, "observation_run_id": str(observation_run_id),
              "collection_run_id": source.get("collection_run_id"),
              "retrieval_run_id": summary.get("retrieval_run_id"),
              "review_queue_run_id": os.getenv("GITHUB_RUN_ID"), "git_sha": os.getenv("GITHUB_SHA"),
              "captured_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Raw candidate index by PDF hash and exact-SKU membership only; no candidate selection, model matching, numeric comparison, or assessment",
              "status": "PASS", "queue_state": "RAW_CANDIDATES_READY_FOR_REVIEW",
              "sku_population_count": len(sku_coverage), "skus_without_support_document": skus_without_documents,
              "skus_without_review_document": skus_without_review_document,
              "sku_document_coverage": sku_coverage, "sku_document_count": len(sku_docs), "unique_pdf_count": len(entries),
              "flagged_pdf_count": sum(bool(entry["review_flags"]) for entry in entries),
              "entries": entries, "table": table}
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "review-queue.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## TV EnergyGuide raw-candidate review\n\n")
            stream.write(f"Target SKUs: **{len(sku_coverage)}**; with no Support document: **{len(skus_without_documents)}**; SKU-document links: **{len(sku_docs)}**; unique PDFs: **{len(entries)}**; PDFs with review flags: **{report['flagged_pdf_count']}**. No pass/fail finding or value selection was made.\n\n")
            if skus_without_documents:
                stream.write("Exact SKUs with no Support-declared label PDF: " + ", ".join(f"`{sku}`" for sku in skus_without_documents) + "\n\n")
            stream.write("| PDF SHA-256 prefix | Exact SKU(s) | Model text (source layer) | Annual kWh (source layer/role) | Capacity text | Review flags |\n|---|---|---|---|---|---|\n")
            for row in table:
                cells = [row["pdf_sha256"][:12], ", ".join(row["exact_skus"]),
                         "; ".join(f"{x['value_raw']} [{x['evidence_layer']}]" for x in row["model_evidence_raw"]),
                         "; ".join(f"{x['value_raw']} [{x['evidence_layer']}; {x['role']}]" for x in row["annual_evidence_raw"]),
                         "; ".join(row["capacity_raw"]), ", ".join(row["review_flags"]) or "none"]
                stream.write("| " + " | ".join(cell.replace("|", "\\|").replace("\n", " ") for cell in cells) + " |\n")
            stream.write("\n`models_raw` contains text-like tokens near an explicit printed Models/Model label; all other model-shaped tokens remain separately preserved in the JSON review artifact. Annual kWh rows require nearby yearly-electricity wording and are still unreviewed candidates.\n")
    print(json.dumps({"status": "PASS", "sku_document_count": len(sku_docs), "unique_pdf_count": len(entries),
                      "flagged_pdf_count": report["flagged_pdf_count"],
                      "review_table": table,
                      "skus_without_support_document": skus_without_documents,
                      "skus_without_review_document": skus_without_review_document},
                     ensure_ascii=False, sort_keys=True), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation-root", required=True)
    parser.add_argument("--observation-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    review(args.observation_root, args.observation_run_id, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

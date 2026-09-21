"""Observe EnergyGuide PDF text, layout, and OCR without selecting fields."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

import pymupdf
from energyguide_fields import label_candidates, annual_layout_candidates
from runner_probe import safe_url


CONTRACT = "G3_DISHWASHER_ENERGYGUIDE_OBSERVATION_V1"
US_HEADING = re.compile(r"energy\s*guide", re.I)
CANADA_HEADING = re.compile(r"ener\s*guide", re.I)


def _json(path: Path) -> Any:
    return json.loads(path.read_bytes())


def verified_pdf_population(root: str | Path, retrieval_run_id: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Verify the successful retrieval artifact and index one copy per PDF hash."""
    base = Path(root)
    report = _json(base / "energyguide-summary.json")
    if report.get("status") != "PASS" or str(report.get("retrieval_run_id")) != str(retrieval_run_id):
        raise ValueError("Dishwasher EnergyGuide artifact is not the requested successful run")
    if report.get("failed_url_count") != 0:
        raise ValueError("Dishwasher EnergyGuide artifact includes failed PDF URLs")
    by_hash: dict[str, dict[str, Any]] = {}
    by_url = {item.get("url"): item for item in report.get("url_observations", [])}
    if len(by_url) != report.get("url_count"):
        raise ValueError("EnergyGuide URL observation count differs from the source summary")
    sku_documents = []
    for record in report.get("records", []):
        sku = record.get("exact_sku")
        url = record.get("url")
        retrieval = record.get("retrieval")
        observation = by_url.get(url)
        if not isinstance(sku, str) or not isinstance(retrieval, dict) or not observation:
            raise ValueError("EnergyGuide document record lacks exact SKU or retrieval provenance")
        if observation.get("status") != "RETRIEVED_VALID_PDF" or retrieval.get("sha256") != observation.get("sha256"):
            raise ValueError("EnergyGuide SKU document is not linked to a retrieved PDF hash")
        digest = observation.get("sha256")
        relative = observation.get("path")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest) or not isinstance(relative, str):
            raise ValueError("EnergyGuide PDF hash or artifact path is invalid")
        pdf_path = (base / relative).resolve()
        if not pdf_path.is_relative_to(base.resolve()) or not pdf_path.is_file():
            raise ValueError("EnergyGuide PDF artifact path is missing or unsafe")
        actual = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError("EnergyGuide PDF bytes do not match the recorded SHA-256")
        item = by_hash.setdefault(digest, {"pdf_sha256": digest, "path": pdf_path,
                                           "source_urls": set(), "sku_documents": []})
        item["source_urls"].add(url)
        item["sku_documents"].append({"exact_sku": sku, "source_document_index": record.get("source_document_index"),
                                       "url": safe_url(url), "name_raw": record.get("name_raw"),
                                       "type_raw": record.get("type_raw")})
        sku_documents.append({"exact_sku": sku, "source_document_index": record.get("source_document_index"),
                              "pdf_sha256": digest, "url": safe_url(url)})
    if len(by_hash) != report.get("pdf_hash_count"):
        raise ValueError("Unique PDF hash count differs from the retrieval source summary")
    return by_hash, {"retrieval_run_id": str(retrieval_run_id), "sku_document_count": len(sku_documents),
                     "unique_pdf_count": len(by_hash), "sku_documents": sku_documents}


def embedded_lines(page: Any, page_number: int) -> list[dict[str, Any]]:
    rows = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            raw = "".join(span.get("text", "") for span in spans)
            if not raw:
                continue
            boxes = [span["bbox"] for span in spans if span.get("bbox")]
            if not boxes:
                continue
            rows.append({"page": page_number, "text": raw,
                         "bbox": [min(box[0] for box in boxes), min(box[1] for box in boxes),
                                  max(box[2] for box in boxes), max(box[3] for box in boxes)],
                         "engine": "PyMuPDF", "font_sizes_raw": [span.get("size") for span in spans]})
    return sorted(rows, key=lambda row: (row["bbox"][1], row["bbox"][0]))


def heading_observations(spans: list[dict[str, Any]]) -> dict[str, Any]:
    us = []
    canada = []
    for index, span in enumerate(spans):
        text = span["text"]
        row = {"span_index": index, "text_raw": text, "page": span["page"], "bbox": span["bbox"],
               "engine": span["engine"]}
        if US_HEADING.search(text):
            us.append(row)
        if CANADA_HEADING.search(text) and not US_HEADING.search(text):
            canada.append(row)
    return {"us_energyguide_heading_candidates": us, "canada_energuide_heading_candidates": canada,
            "region_boundaries": "NOT_DERIVED", "annual_energy_value_selection": "NOT_EVALUATED",
            "model_identity_matching": "NOT_EVALUATED"}


def observe_pdf(item: dict[str, Any], output: Path, engine: Any) -> dict[str, Any]:
    digest = item["pdf_sha256"]
    raw = item["path"].read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest or not raw.startswith(b"%PDF-"):
        raise ValueError("EnergyGuide source PDF hash or signature is invalid")
    target = output / "pdf" / digest
    target.mkdir(parents=True, exist_ok=True)
    pages = []
    all_spans = []
    with pymupdf.open(stream=raw, filetype="pdf") as document:
        if document.page_count == 0:
            raise ValueError("EnergyGuide PDF has no pages")
        for page_number, page in enumerate(document, start=1):
            spans = embedded_lines(page, page_number)
            text_source = "EMBEDDED_TEXT" if any(span["text"].strip() for span in spans) else "IMAGE_OCR"
            render = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
            preview_name = f"page-{page_number:02d}-2x.png"
            render.save(target / preview_name)
            if text_source == "IMAGE_OCR":
                result = engine(str(target / preview_name))
                texts = [] if result.txts is None else list(result.txts)
                boxes = [] if result.boxes is None else list(result.boxes)
                scores = [] if result.scores is None else list(result.scores)
                if not (len(texts) == len(boxes) == len(scores)):
                    raise ValueError("RapidOCR returned mismatched text, box, and score arrays")
                spans = []
                for text, box, score in zip(texts, boxes, scores):
                    points = box.tolist() if hasattr(box, "tolist") else box
                    normalized = [[float(point[0]) / 2, float(point[1]) / 2] for point in points]
                    spans.append({"page": page_number, "text": str(text),
                                  "bbox": [min(point[0] for point in normalized), min(point[1] for point in normalized),
                                           max(point[0] for point in normalized), max(point[1] for point in normalized)],
                                  "polygon": normalized, "confidence_raw": float(score), "engine": "RapidOCR"})
                spans.sort(key=lambda span: (span["bbox"][1], span["bbox"][0]))
            all_spans.extend(spans)
            text = "\n".join(span["text"] for span in spans)
            fields = label_candidates(text, "RapidOCR" if text_source == "IMAGE_OCR" else "PyMuPDF", digest) if text.strip() else None
            layout = annual_layout_candidates(spans, digest)
            pages.append({"page": page_number, "width_points": float(page.rect.width),
                          "height_points": float(page.rect.height), "text_source": text_source,
                          "span_count": len(spans), "text_observation": "TEXT_OBSERVED" if text.strip() else "NO_TEXT_OBSERVED",
                          "text_raw": text, "spans_raw": spans, "fields_raw": fields,
                          "annual_layout_candidates_raw": layout["annual_layout_candidates"],
                          "preview_path": f"pdf/{digest}/{preview_name}"})
    return {"pdf_sha256": digest, "byte_count": len(raw), "page_count": len(pages),
            "source_urls": sorted(safe_url(url) for url in item["source_urls"]),
            "sku_documents": item["sku_documents"], "pages": pages,
            "label_heading_observations": heading_observations(all_spans),
            "field_selection": "NOT_EVALUATED", "identity_matching": "NOT_EVALUATED",
            "compliance": "NOT_EVALUATED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrieval-root", required=True)
    parser.add_argument("--retrieval-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    pdfs, source = verified_pdf_population(args.retrieval_root, args.retrieval_run_id)
    from rapidocr import RapidOCR
    engine = RapidOCR(params={"EngineConfig.onnxruntime.intra_op_num_threads": 1,
                              "EngineConfig.onnxruntime.inter_op_num_threads": 1})
    destination = Path(args.out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "sku-document-index.json").write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    observations = []
    failures = []
    for index, (digest, item) in enumerate(sorted(pdfs.items()), start=1):
        try:
            observation = observe_pdf(item, destination, engine)
            safe_digest = digest
            path = destination / "pdf" / safe_digest / "observation.json"
            path.write_text(json.dumps(observation, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            observations.append({"pdf_sha256": digest, "status": "OBSERVED", "observation_path": f"pdf/{safe_digest}/observation.json",
                                "page_count": observation["page_count"],
                                "text_observed_pages": sum(p["text_observation"] == "TEXT_OBSERVED" for p in observation["pages"]),
                                "us_heading_candidate_count": len(observation["label_heading_observations"]["us_energyguide_heading_candidates"]),
                                "canada_heading_candidate_count": len(observation["label_heading_observations"]["canada_energuide_heading_candidates"])})
        except Exception as error:
            failures.append({"pdf_sha256": digest, "error_type": type(error).__name__,
                             "error": str(error).splitlines()[0][:300]})
        print(json.dumps({"processed_unique_pdf": index, "total_unique_pdfs": len(pdfs),
                          "status": "FAILED" if failures and failures[-1]["pdf_sha256"] == digest else "OBSERVED",
                          "sha256": digest}, sort_keys=True), flush=True)
    report = {"contract": CONTRACT, "source": source,
              "retrieval_run_id": args.retrieval_run_id, "observation_run_id": os.getenv("GITHUB_RUN_ID"),
              "git_sha": os.getenv("GITHUB_SHA"), "captured_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Hash-verified dishwasher EnergyGuide source text, layout, and unreadable-page OCR observation only",
              "status": "PASS" if not failures and len(observations) == len(pdfs) else "FAILED",
              "field_selection": "NOT_EVALUATED", "identity_matching": "NOT_EVALUATED",
              "compliance": "NOT_EVALUATED", "observed_pdf_count": len(observations),
              "failed_pdf_count": len(failures), "observations": observations, "failures": failures}
    (destination / "observation-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Dishwasher EnergyGuide text and layout observation\n\n")
            stream.write(f"Status: **{report['status']}**; SKU document rows: {source['sku_document_count']}; unique PDFs observed: {len(observations)}; failures: {len(failures)}\n\n")
            stream.write("No annual-energy value selection, model matching, or compliance assessment was performed.\n\n")
            for failure in failures:
                stream.write(f"- `{failure['pdf_sha256']}`: {failure['error']}\n")
    print(json.dumps({"status": report["status"], "sku_document_count": source["sku_document_count"],
                      "unique_pdf_count": len(observations), "failed_pdf_count": len(failures)}, sort_keys=True), flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

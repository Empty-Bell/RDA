"""Observe hash-verified TV EnergyGuide text and layout; never select values."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

import pymupdf
from energyguide_fields import label_candidates, annual_layout_candidates
from g3_dishTV_energyguide_observe import embedded_lines, heading_observations, verified_pdf_population
from runner_probe import safe_url


CONTRACT = "G3_TV_ENERGYGUIDE_OBSERVATION_V1"


def observe_pdf(item, output, engine):
    digest = item["pdf_sha256"]
    raw = item["path"].read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest or not raw.startswith(b"%PDF-"):
        raise ValueError("TV EnergyGuide source PDF hash or signature is invalid")
    target = output / "pdf" / digest
    target.mkdir(parents=True, exist_ok=True)
    pages, all_spans = [], []
    with pymupdf.open(stream=raw, filetype="pdf") as document:
        if not document.page_count:
            raise ValueError("TV EnergyGuide PDF has no pages")
        for page_number, page in enumerate(document, start=1):
            spans = embedded_lines(page, page_number)
            text_source = "EMBEDDED_TEXT" if any(span["text"].strip() for span in spans) else "IMAGE_OCR"
            embedded_spans = spans if text_source == "EMBEDDED_TEXT" else []
            preview_name = f"page-{page_number:02d}-2x.png"
            page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False).save(target / preview_name)

            def run_ocr():
                result = engine(str(target / preview_name))
                texts = [] if result.txts is None else list(result.txts)
                boxes = [] if result.boxes is None else list(result.boxes)
                scores = [] if result.scores is None else list(result.scores)
                if not (len(texts) == len(boxes) == len(scores)):
                    raise ValueError("RapidOCR returned mismatched text, box, and score arrays")
                detections = []
                for text, box, score in zip(texts, boxes, scores):
                    points = box.tolist() if hasattr(box, "tolist") else box
                    normalized = [[float(point[0]) / 2, float(point[1]) / 2] for point in points]
                    detections.append({"page": page_number, "text": str(text),
                                       "bbox": [min(point[0] for point in normalized), min(point[1] for point in normalized),
                                                max(point[0] for point in normalized), max(point[1] for point in normalized)],
                                       "polygon": normalized, "confidence_raw": float(score), "engine": "RapidOCR"})
                return sorted(detections, key=lambda span: (span["bbox"][1], span["bbox"][0]))

            embedded_text = "\n".join(span["text"] for span in spans)
            embedded_fields = label_candidates(embedded_text, "PyMuPDF", digest) if embedded_text.strip() else None
            has_annual = bool(embedded_fields and any(candidate.get("role") == "ANNUAL_CAPTION_CONTEXT"
                                                       for candidate in embedded_fields.get("energy_candidates_raw", [])))
            complement = None
            if text_source == "IMAGE_OCR":
                spans = run_ocr()
            elif not has_annual:
                ocr_spans = run_ocr()
                ocr_text = "\n".join(span["text"] for span in ocr_spans)
                ocr_fields = label_candidates(ocr_text, "RapidOCR", digest) if ocr_text.strip() else None
                ocr_layout = annual_layout_candidates(ocr_spans, digest)
                complement = {"reason": "NO_ANNUAL_ENERGY_CANDIDATE_IN_EMBEDDED_TEXT",
                              "text_raw": ocr_text, "spans_raw": ocr_spans, "fields_raw": ocr_fields,
                              "annual_layout_candidates_raw": ocr_layout["annual_layout_candidates"],
                              "selection": "NOT_EVALUATED"}
            all_spans.extend(spans)
            if complement:
                all_spans.extend(complement["spans_raw"])
            text = "\n".join(span["text"] for span in spans)
            fields = label_candidates(text, "RapidOCR" if text_source == "IMAGE_OCR" else "PyMuPDF", digest) if text.strip() else None
            layout = annual_layout_candidates(spans, digest)
            pages.append({"page": page_number, "width_points": float(page.rect.width),
                          "height_points": float(page.rect.height), "text_source": text_source,
                          "span_count": len(spans), "text_observation": "TEXT_OBSERVED" if text.strip() else "NO_TEXT_OBSERVED",
                          "text_raw": text, "spans_raw": spans, "fields_raw": fields,
                          "embedded_spans_raw": embedded_spans, "ocr_complement_raw": complement,
                          "annual_layout_candidates_raw": layout["annual_layout_candidates"],
                          "preview_path": f"pdf/{digest}/{preview_name}"})
    return {"pdf_sha256": digest, "byte_count": len(raw), "page_count": len(pages),
            "source_urls": sorted(safe_url(url) for url in item["source_urls"]), "sku_documents": item["sku_documents"],
            "pages": pages, "label_heading_observations": heading_observations(all_spans),
            "ocr_complement_pages": sum(page.get("ocr_complement_raw") is not None for page in pages),
            "field_selection": "NOT_EVALUATED", "model_matching": "NOT_EVALUATED",
            "assessment": "NOT_EVALUATED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrieval-root", required=True)
    parser.add_argument("--retrieval-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    pdfs, source = verified_pdf_population(args.retrieval_root, args.retrieval_run_id, allow_nasca_drm=True)
    retrieval_report = json.loads((Path(args.retrieval_root) / "energyguide-summary.json").read_bytes())
    source["collection_run_id"] = retrieval_report.get("collection_run_id")
    source["sku_population_count"] = retrieval_report.get("sku_population_count")
    source["sku_document_coverage"] = retrieval_report.get("sku_document_coverage", [])
    if len(source["sku_document_coverage"]) != source["sku_population_count"]:
        raise ValueError("TV label document coverage does not include the exact PDP population")
    from rapidocr import RapidOCR
    engine = RapidOCR(params={"EngineConfig.onnxruntime.intra_op_num_threads": 1,
                              "EngineConfig.onnxruntime.inter_op_num_threads": 1})
    destination = Path(args.out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "sku-document-index.json").write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    observations, failures = [], []
    for index, (digest, item) in enumerate(sorted(pdfs.items()), start=1):
        try:
            observation = observe_pdf(item, destination, engine)
            path = destination / "pdf" / digest / "observation.json"
            path.write_text(json.dumps(observation, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            observations.append({"pdf_sha256": digest, "status": "OBSERVED",
                                 "observation_path": f"pdf/{digest}/observation.json",
                                 "page_count": observation["page_count"],
                                 "ocr_complement_pages": observation.get("ocr_complement_pages", 0),
                                 "text_observed_pages": sum(p["text_observation"] == "TEXT_OBSERVED" for p in observation["pages"]),
                                 "us_heading_candidate_count": len(observation["label_heading_observations"]["us_energyguide_heading_candidates"]),
                                 "canada_heading_candidate_count": len(observation["label_heading_observations"]["canada_energuide_heading_candidates"])})
        except Exception as error:
            failures.append({"pdf_sha256": digest, "error_type": type(error).__name__,
                             "error": str(error).splitlines()[0][:300]})
            print(json.dumps({"observation_failure": digest, "error_type": type(error).__name__,
                              "error": str(error).splitlines()[0][:300]}, sort_keys=True), flush=True)
        print(json.dumps({"processed_unique_pdf": index, "total_unique_pdfs": len(pdfs),
                          "status": "FAILED" if failures and failures[-1]["pdf_sha256"] == digest else "OBSERVED",
                          "sha256": digest}, sort_keys=True), flush=True)
    report = {"contract": CONTRACT, "source": source,
              "retrieval_run_id": str(args.retrieval_run_id), "observation_run_id": os.getenv("GITHUB_RUN_ID"),
              "git_sha": os.getenv("GITHUB_SHA"), "captured_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Hash-verified TV EnergyGuide source text, layout, and unreadable-page OCR observations only",
              "status": "FAILED" if failures or len(observations) != len(pdfs) else "PARTIAL" if source.get("unreadable_documents") else "PASS",
              "field_selection": "NOT_EVALUATED", "identity_matching": "NOT_EVALUATED",
              "assessment": "NOT_EVALUATED", "observed_pdf_count": len(observations),
              "failed_pdf_count": len(failures), "observations": observations, "failures": failures}
    (destination / "observation-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## TV EnergyGuide observation\n\n")
            stream.write(f"Status: **{report['status']}**; SKU-document rows: {source['sku_document_count']}; unique PDFs: {len(observations)}; failures: {len(failures)}\n\n")
            stream.write(f"Pages OCR-complemented because embedded text lacked annual kWh: {sum(x.get('ocr_complement_pages', 0) for x in observations)}\n\n")
            stream.write("Only unreadable pages use OCR. Model, annual-energy, and capacity selection and all compliance assessment remain disabled.\n\n")
            for failure in failures:
                stream.write(f"- `{failure['pdf_sha256']}`: {failure['error']}\n")
    print(json.dumps({"status": report["status"], "sku_document_count": source["sku_document_count"],
                      "unique_pdf_count": len(observations), "failed_pdf_count": len(failures)}, sort_keys=True), flush=True)
    return 0 if report["status"] in ("PASS", "PARTIAL") else 1


if __name__ == "__main__":
    raise SystemExit(main())

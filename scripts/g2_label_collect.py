"""Bounded raw EnergyGuide observation for already verified PDP samples."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from energyguide_fields import annual_layout_candidates, label_candidates
from g2_label_plan import declared_energyguide_documents
from source_contract import energyguide_ocr_reason


def _save(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def collect_energyguide_documents(results: list[dict[str, Any]], output: Path) -> list[dict[str, Any]]:
    """Fetch every exact-SKU Support document and retain unselected candidates."""
    import pymupdf
    from playwright.sync_api import sync_playwright

    output.mkdir(parents=True, exist_ok=False)
    plan = declared_energyguide_documents(results)
    collected = []
    with sync_playwright() as playwright:
        requests = playwright.request.new_context()
        for row in plan["rows"]:
            for document in row["documents"]:
                sku = row["exact_sku"]
                folder = output / sku / str(document["source_document_index"])
                folder.mkdir(parents=True)
                result = {
                    "exact_sku": sku,
                    "source_document_index": document["source_document_index"],
                    "requested_url": document["url"],
                    "status": "FAILED",
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    response = requests.get(document["url"], timeout=30000)
                    raw = response.body()
                    (folder / "energyguide-original.pdf").write_bytes(raw)
                    if response.status != 200 or not raw.startswith(b"%PDF-"):
                        raise ValueError("EnergyGuide response is not a valid PDF")
                    pdf_hash = hashlib.sha256(raw).hexdigest()
                    parsed = pymupdf.open(stream=raw, filetype="pdf")
                    extracted = "\n".join(page.get_text() for page in parsed)
                    embedded_spans = [
                        {"page": page_index, "bbox": list(block[:4]), "text": block[4], "engine": "PyMuPDF"}
                        for page_index, page in enumerate(parsed)
                        for block in page.get_text("blocks")
                        if block[6] == 0
                    ]
                    _save(folder / "energyguide-embedded-spans.json", embedded_spans)
                    ocr_texts, ocr_spans, fallback_reason, engine_name = [], [], None, "PyMuPDF"
                    if energyguide_ocr_reason(extracted):
                        import cv2
                        from rapidocr import RapidOCR

                        cv2.setNumThreads(1)
                        fallback_reason = energyguide_ocr_reason(extracted)
                        image_path = folder / "energyguide-ocr-2x.png"
                        parsed[0].get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(image_path)
                        engine = RapidOCR(params={"EngineConfig.onnxruntime.intra_op_num_threads": 1,
                                                  "EngineConfig.onnxruntime.inter_op_num_threads": 1})
                        ocr = engine(str(image_path))
                        ocr_texts = list(ocr.txts or [])
                        ocr_spans = [{"page": 0, "text": text,
                                      "bbox": [[float(x) / 2, float(y) / 2] for x, y in box],
                                      "confidence": float(score), "engine": "RapidOCR"}
                                     for text, box, score in zip(ocr.txts, ocr.boxes, ocr.scores)]
                        if not ocr_texts or len(ocr_texts) != len(ocr_spans):
                            raise ValueError("EnergyGuide OCR observations incomplete")
                        _save(folder / "energyguide-ocr-texts.json", ocr_texts)
                        _save(folder / "energyguide-ocr-spans.json", ocr_spans)
                        engine_name = "RapidOCR"
                    evidence_text = "\n".join(ocr_texts) if ocr_texts else extracted
                    candidates = label_candidates(evidence_text, engine_name, pdf_hash)
                    layout = annual_layout_candidates(ocr_spans if ocr_texts else embedded_spans, pdf_hash)
                    if not candidates["energy_candidates_raw"]:
                        raise ValueError("EnergyGuide numeric kWh candidates unavailable")
                    _save(folder / "energyguide-field-candidates.json", candidates)
                    _save(folder / "energyguide-layout-candidates.json", layout)
                    result.update({
                        "status": "OBSERVED_SOURCE_PDF",
                        "final_url": response.url,
                        "http_status": response.status,
                        "content_type": response.headers.get("content-type"),
                        "sha256": pdf_hash,
                        "embedded_text": extracted,
                        "extraction_engine": engine_name,
                        "fallback_reason": fallback_reason,
                        "ocr_raw_texts": ocr_texts,
                        "ocr_scale": 2 if ocr_texts else None,
                        "pdf_page_count": len(parsed),
                        "field_parser_contract": "CANDIDATE_EXTRACTION_ONLY",
                    })
                except Exception as error:
                    result["error_class"] = type(error).__name__
                finally:
                    _save(folder / "result.json", result)
                    collected.append(result)
        requests.dispose()
    return collected

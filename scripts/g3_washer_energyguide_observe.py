"""Observe hash-verified Washer EnergyGuide text and layout; never select values."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from g3_dishwasher_energyguide_observe import observe_pdf, verified_pdf_population


CONTRACT = "G3_WASHER_ENERGYGUIDE_OBSERVATION_V1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrieval-root", required=True)
    parser.add_argument("--retrieval-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    pdfs, source = verified_pdf_population(args.retrieval_root, args.retrieval_run_id)
    retrieval_report = json.loads((Path(args.retrieval_root) / "energyguide-summary.json").read_bytes())
    source["sku_population_count"] = retrieval_report.get("sku_population_count")
    source["sku_document_coverage"] = retrieval_report.get("sku_document_coverage", [])
    if len(source["sku_document_coverage"]) != source["sku_population_count"]:
        raise ValueError("Washer label document coverage does not include the exact PDP population")
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
              "retrieval_run_id": str(args.retrieval_run_id), "observation_run_id": os.getenv("GITHUB_RUN_ID"),
              "git_sha": os.getenv("GITHUB_SHA"), "captured_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Hash-verified Washer EnergyGuide source text, layout, and unreadable-page OCR observations only",
              "status": "PASS" if not failures and len(observations) == len(pdfs) else "FAILED",
              "field_selection": "NOT_EVALUATED", "identity_matching": "NOT_EVALUATED",
              "assessment": "NOT_EVALUATED", "observed_pdf_count": len(observations),
              "failed_pdf_count": len(failures), "observations": observations, "failures": failures}
    (destination / "observation-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Washer EnergyGuide observation\n\n")
            stream.write(f"Status: **{report['status']}**; SKU-document rows: {source['sku_document_count']}; unique PDFs: {len(observations)}; failures: {len(failures)}\n\n")
            stream.write("Only unreadable pages use OCR. Model, annual-energy, and capacity selection and all compliance assessment remain disabled.\n\n")
            for failure in failures:
                stream.write(f"- `{failure['pdf_sha256']}`: {failure['error']}\n")
    print(json.dumps({"status": report["status"], "sku_document_count": source["sku_document_count"],
                      "unique_pdf_count": len(observations), "failed_pdf_count": len(failures)}, sort_keys=True), flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

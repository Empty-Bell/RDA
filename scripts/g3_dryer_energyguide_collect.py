"""Retrieve and hash Dryer PDP Support-declared EnergyGuide PDFs; no OCR or assessment."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from runner_probe import safe_url, valid_pdf


CONTRACT = "G3_DRYER_ENERGYGUIDE_RETRIEVAL_V1"


def read_json(path):
    return json.loads(Path(path).read_bytes())


def load_documents(collection_root, collection_run_id):
    root = Path(collection_root)
    summary = read_json(root / "collection-summary.json")
    if summary.get("status") != "PASS" or str(summary.get("collection_run_id")) != str(collection_run_id):
        raise ValueError("Dryer PDP collection artifact is not the requested successful run")
    expected = summary.get("coverage", {}).get("population_count")
    results = sorted(root.glob("pdp/*/result.json"))
    if not isinstance(expected, int) or len(results) != expected:
        raise ValueError("Dryer collection artifact does not contain full PDP evidence")
    declarations, seen = [], set()
    sku_coverage = []
    identity = None
    for path in results:
        result = read_json(path)
        sku = result.get("exact_sku")
        if not isinstance(sku, str) or not sku or sku in seen or result.get("status") != "VERIFIED_EXACT_IDENTITY":
            raise ValueError("Dryer collection result is not a unique verified exact SKU")
        seen.add(sku)
        user_agent = result.get("browser_identity", {}).get("user_agent")
        if not isinstance(user_agent, str) or "Chrome/" not in user_agent or "HeadlessChrome/" in user_agent:
            raise ValueError("Dryer collection has no realistic desktop browser identity")
        if identity is None:
            identity = user_agent
        elif identity != user_agent:
            raise ValueError("Dryer collection mixes browser identities")
        docs = result.get("pdp_facts_raw", {}).get("energyguide_documents")
        if not isinstance(docs, list):
            raise ValueError("Dryer Support document list is invalid")
        sku_coverage.append({"exact_sku": sku, "support_document_count": len(docs),
                             "state": "DOCUMENTS_DECLARED" if docs else "NO_SUPPORT_DOCUMENT_DECLARED"})
        for index, doc in enumerate(docs):
            url = doc.get("url") if isinstance(doc, dict) else None
            parts = urlsplit(url) if isinstance(url, str) else None
            if (not parts or parts.scheme != "https" or not parts.hostname
                    or not (parts.hostname == "samsung.com" or parts.hostname.endswith(".samsung.com"))):
                raise ValueError("Dryer Support EnergyGuide URL must be HTTPS on samsung.com")
            declarations.append({"exact_sku": sku, "source_document_index": index,
                                 "name_raw": doc.get("name"), "type_raw": doc.get("type"), "url": url})
    if identity is None:
        raise ValueError("Dryer collection contains no PDP results")
    return declarations, identity, sku_coverage


def retrieve(url, user_agent):
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "application/pdf,*/*;q=0.8"})
    with urlopen(request, timeout=45) as response:
        return response.read(), response.url, response.headers.get_content_type(), response.status


def collect(declarations, output, user_agent):
    destination = Path(output)
    pdf_root = destination / "pdf"
    pdf_root.mkdir(parents=True, exist_ok=True)
    by_url = {}
    for declaration in declarations:
        by_url.setdefault(declaration["url"], {"url": declaration["url"], "status": "FAILED"})
    for url, observation in by_url.items():
        try:
            body, final_url, content_type, status = retrieve(url, user_agent)
            final = urlsplit(final_url)
            if (status != 200 or content_type != "application/pdf" or not valid_pdf(body)
                    or final.scheme != "https" or not final.hostname
                    or not (final.hostname == "samsung.com" or final.hostname.endswith(".samsung.com"))):
                raise ValueError("EnergyGuide response is not an HTTPS Samsung PDF")
            digest = hashlib.sha256(body).hexdigest()
            path = pdf_root / f"{digest}.pdf"
            if path.exists() and path.read_bytes() != body:
                raise ValueError("EnergyGuide hash path has conflicting bytes")
            path.write_bytes(body)
            observation.update(status="RETRIEVED_VALID_PDF", final_url=safe_url(final_url),
                               content_type=content_type, http_status=status, byte_count=len(body),
                               sha256=digest, path=f"pdf/{path.name}")
        except Exception as error:
            observation["error"] = str(error).splitlines()[0][:300]
    records = [{**declaration, "retrieval": {key: value for key, value in by_url[declaration["url"]].items() if key != "url"}}
               for declaration in declarations]
    return {"records": records, "url_count": len(by_url),
            "pdf_hash_count": len({x["sha256"] for x in by_url.values() if x.get("sha256")}),
            "failed_url_count": sum(x["status"] == "FAILED" for x in by_url.values()),
            "url_observations": list(by_url.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--collection-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    declarations, user_agent, sku_coverage = load_documents(args.collection_root, args.collection_run_id)
    collected = collect(declarations, args.out, user_agent)
    report = {"contract": CONTRACT,
              "scope": "Exact-SKU PDP Support-declared Dryer PDF retrieval and byte hashing only; no OCR, selection, matching, or assessment",
              "collection_run_id": str(args.collection_run_id), "retrieval_run_id": os.getenv("GITHUB_RUN_ID"),
              "git_sha": os.getenv("GITHUB_SHA"), "captured_at": datetime.now(timezone.utc).isoformat(),
              "status": "PASS" if collected["failed_url_count"] == 0 else "FAILED",
              "sku_document_coverage": sku_coverage, "sku_population_count": len(sku_coverage), **collected}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "energyguide-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Dryer EnergyGuide PDF retrieval\n\n")
            missing_docs = [row["exact_sku"] for row in sku_coverage if row["state"] == "NO_SUPPORT_DOCUMENT_DECLARED"]
            stream.write(f"Status: **{report['status']}**; target SKUs: {len(sku_coverage)}; declared docs: {len(declarations)}; unique URLs: {report['url_count']}; PDFs: {report['pdf_hash_count']}\n\n")
            stream.write("SKUs with no PDP Support-declared document: " + (", ".join(f"`{sku}`" for sku in missing_docs) if missing_docs else "none") + "\n\n")
            for row in report["url_observations"]:
                if row["status"] == "FAILED":
                    stream.write(f"- `{safe_url(row['url'])}`: {row.get('error', 'retrieval failed')}\n")
    for row in report["url_observations"]:
        if row["status"] == "FAILED":
            print(json.dumps({"failed_energyguide_url": safe_url(row["url"]),
                              "error": row.get("error", "retrieval failed")}, sort_keys=True), flush=True)
    print(json.dumps({"status": report["status"], "declared_document_count": len(declarations),
                      "url_count": report["url_count"], "pdf_hash_count": report["pdf_hash_count"]}, sort_keys=True), flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

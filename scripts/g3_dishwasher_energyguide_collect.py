"""Retrieve and hash Support-declared dishwasher EnergyGuide PDFs; do not interpret them."""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from runner_probe import safe_url, valid_pdf


CONTRACT = "G3_DISHWASHER_ENERGYGUIDE_RETRIEVAL_V1"


def _json(path: Path) -> Any:
    return json.loads(path.read_bytes())


def load_verified_documents(collection_root: str | Path, collection_run_id: str) -> tuple[list[dict[str, Any]], str]:
    """Return every exact-SKU Support declaration, retaining no PDF selection policy."""
    root = Path(collection_root)
    summary = _json(root / "collection-summary.json")
    if summary.get("status") != "PASS" or str(summary.get("collection_run_id")) != str(collection_run_id):
        raise ValueError("Dishwasher collection artifact is not the requested successful run")
    expected = summary.get("coverage", {}).get("population_count")
    results = sorted(root.glob("pdp/*/result.json"))
    if not isinstance(expected, int) or len(results) != expected:
        raise ValueError("Dishwasher collection artifact does not contain full PDP evidence")
    declarations: list[dict[str, Any]] = []
    identity: str | None = None
    seen_skus: set[str] = set()
    for path in results:
        result = _json(path)
        sku = result.get("exact_sku")
        if not isinstance(sku, str) or not sku or sku in seen_skus or result.get("status") != "VERIFIED_EXACT_IDENTITY":
            raise ValueError("Dishwasher collection result is not a unique verified exact SKU")
        seen_skus.add(sku)
        user_agent = result.get("browser_identity", {}).get("user_agent")
        if not isinstance(user_agent, str) or "Chrome/" not in user_agent or "HeadlessChrome/" in user_agent:
            raise ValueError("Dishwasher collection has no realistic desktop browser identity")
        if identity is None:
            identity = user_agent
        elif identity != user_agent:
            raise ValueError("Dishwasher collection mixes browser identities")
        documents = result.get("pdp_facts_raw", {}).get("energyguide_documents")
        if not isinstance(documents, list):
            raise ValueError("Dishwasher exact Support document collection is invalid")
        for index, document in enumerate(documents):
            url = document.get("url") if isinstance(document, dict) else None
            parts = urlsplit(url) if isinstance(url, str) else None
            if not parts or parts.scheme != "https" or not parts.netloc:
                raise ValueError("Dishwasher Support EnergyGuide URL must be HTTPS")
            declarations.append({"exact_sku": sku, "source_document_index": index,
                                 "name_raw": document.get("name"), "type_raw": document.get("type"), "url": url})
    if identity is None:
        raise ValueError("Dishwasher collection has no PDP results")
    return declarations, identity


def retrieve(url: str, user_agent: str) -> tuple[bytes, str, str, int]:
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "application/pdf,*/*;q=0.8"})
    with urlopen(request, timeout=60) as response:
        body = response.read()
        return body, response.url, response.headers.get_content_type(), response.status


def collect_documents(declarations: list[dict[str, Any]], output: str | Path, user_agent: str,
                      fetch: Callable[[str, str], tuple[bytes, str, str, int]] = retrieve) -> dict[str, Any]:
    destination = Path(output)
    pdf_root = destination / "pdf"
    pdf_root.mkdir(parents=True, exist_ok=True)
    by_url: dict[str, dict[str, Any]] = {}
    for declaration in declarations:
        by_url.setdefault(declaration["url"], {"url": declaration["url"], "status": "FAILED"})
    for url, observation in by_url.items():
        try:
            body, final_url, content_type, http_status = fetch(url, user_agent)
            if http_status != 200 or content_type != "application/pdf" or not valid_pdf(body):
                raise ValueError("EnergyGuide response is not a valid PDF")
            digest = hashlib.sha256(body).hexdigest()
            path = pdf_root / f"{digest}.pdf"
            if path.exists() and path.read_bytes() != body:
                raise ValueError("EnergyGuide hash path has conflicting bytes")
            path.write_bytes(body)
            observation.update(status="RETRIEVED_VALID_PDF", final_url=safe_url(final_url), content_type=content_type,
                               http_status=http_status, byte_count=len(body), sha256=digest, path=f"pdf/{path.name}")
        except Exception as error:
            observation["error"] = str(error).splitlines()[0][:300]
    records = []
    for declaration in declarations:
        observation = by_url[declaration["url"]]
        records.append({**declaration, "retrieval": {key: value for key, value in observation.items() if key != "url"}})
    hashes = {entry["sha256"] for entry in by_url.values() if entry.get("status") == "RETRIEVED_VALID_PDF"}
    return {"records": records, "url_count": len(by_url), "pdf_hash_count": len(hashes),
            "failed_url_count": sum(entry["status"] == "FAILED" for entry in by_url.values()),
            "url_observations": list(by_url.values())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--collection-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    declarations, user_agent = load_verified_documents(args.collection_root, args.collection_run_id)
    collected = collect_documents(declarations, args.out, user_agent)
    report = {"contract": CONTRACT, "scope": "Exact-SKU Support-declared PDF retrieval and byte hashing only; no OCR, field selection, matching, or assessment",
              "collection_run_id": args.collection_run_id, "retrieval_run_id": os.getenv("GITHUB_RUN_ID"),
              "git_sha": os.getenv("GITHUB_SHA"), "captured_at": datetime.now(timezone.utc).isoformat(),
              "status": "PASS" if collected["failed_url_count"] == 0 else "FAILED", **collected}
    destination = Path(args.out)
    (destination / "energyguide-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Dishwasher EnergyGuide retrieval\n\n")
            stream.write(f"Status: **{report['status']}**; declared documents: {len(declarations)}; unique URLs: {report['url_count']}; byte-distinct PDFs: {report['pdf_hash_count']}\n\n")
            for item in report["url_observations"]:
                if item["status"] == "FAILED":
                    stream.write(f"- `{safe_url(item['url'])}`: {item.get('error', 'unknown retrieval failure')}\n")
    print(json.dumps({"status": report["status"], "declared_document_count": len(declarations), "url_count": report["url_count"], "pdf_hash_count": report["pdf_hash_count"]}, sort_keys=True), flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

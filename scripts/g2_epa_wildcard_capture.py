"""Bounded official EPA source capture; no model matcher or assessment."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import urllib.request


SOURCES = {
    "upc-faq": "https://www.energystar.gov/partner-resources/products_partner_resources/brand-owner/certifying-products/upc/faqs",
    "qpx-doc": "https://www.energystar.gov/sites/default/files/2024-04/XML_Submission_System_Technical_Documentation_0.pdf",
    "refrigerator-template": "https://www.energystar.gov/products/webservices/spec/67",
    "refrigerator-record-2839420": "https://www.energystar.gov/productfinder/product/certified-residential-refrigerators/details/2839420",
    "refrigerator-metadata": "https://data.energystar.gov/api/views/p5st-her9.json",
}


def source_record(name: str, url: str, status: int, content_type: str, body: bytes) -> dict:
    if status != 200 or not body:
        raise ValueError(f"Official source unavailable: {name} ({status})")
    return {
        "name": name,
        "url": url,
        "status": status,
        "content_type": content_type,
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "size_bytes": len(body),
    }


def replay_capture(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    for record in manifest["sources"]:
        raw = (root / (record["name"] + ".bin")).read_bytes()
        if hashlib.sha256(raw).hexdigest() != record["body_sha256"]:
            raise ValueError("Captured source hash does not replay")
    return manifest


def main() -> None:
    out = Path("runtime/g2-epa-wildcard-capture")
    out.mkdir(parents=True, exist_ok=True)
    records = []
    try:
        for name, url in SOURCES.items():
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept": "application/pdf,text/html,application/json;q=0.9,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                body, status, content_type = (
                    response.read(),
                    response.status,
                    response.headers.get("Content-Type", ""),
                )
            record = source_record(name, url, status, content_type, body)
            (out / (name + ".bin")).write_bytes(body)
            records.append(record)
        manifest = {
            "contract": "G2_EPA_WILDCARD_SOURCE_CAPTURE_ONLY_V1",
            "status": "PASS",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "run_id": os.getenv("GITHUB_RUN_ID"),
            "git_sha": os.getenv("GITHUB_SHA"),
            "sources": records,
            "identity_matching": "NOT_EVALUATED",
            "ocr_correction": "NOT_APPLIED",
            "assessment": "NOT_EVALUATED",
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        replay_capture(out)
    except Exception as error:
        failure = {
            "contract": "G2_EPA_WILDCARD_SOURCE_CAPTURE_ONLY_V1",
            "status": "FAIL",
            "error": str(error),
            "sources": records,
        }
        (out / "manifest.json").write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    main()

"""Bounded official EPA source capture; no model matcher or assessment."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error


SOURCES = {
    "upc-faq": "https://www.energystar.gov/partner-resources/products_partner_resources/brand-owner/certifying-products/upc/faqs",
    "qpx-doc": "https://www.energystar.gov/sites/default/files/2024-04/XML_Submission_System_Technical_Documentation_0.pdf",
    "refrigerator-template": "https://www.energystar.gov/products/webservices/spec/67",
    "refrigerator-record-2839420": "https://www.energystar.gov/productfinder/product/certified-residential-refrigerators/details/2839420",
    "refrigerator-metadata": "https://data.energystar.gov/api/views/p5st-her9.json",
    "refrigerator-api-record": "https://data.energystar.gov/resource/p5st-her9.json?$where=pd_id%3D2839420&$limit=2",
}


def project_source(name: str, body: bytes) -> dict:
    """Project source values only; no certification or SKU equivalence decision."""
    if name == "refrigerator-metadata":
        data = json.loads(body)
        if (
            not isinstance(data, dict)
            or data.get("id") != "p5st-her9"
            or not isinstance(data.get("columns"), list)
        ):
            raise ValueError("Refrigerator metadata identity/schema invalid")
        columns = {c.get("fieldName"): c for c in data["columns"] if isinstance(c, dict)}
        required = ("model_number", "pd_id", "upc", "markets", "additional_model_information")
        if any(key not in columns for key in required):
            raise ValueError("Refrigerator identity columns missing")
        return {
            "id": data["id"],
            "name": data.get("name"),
            "columns": {
                key: {field: columns[key].get(field) for field in ("description", "dataTypeName")}
                for key in required
            },
        }
    if name == "refrigerator-api-record":
        rows = json.loads(body)
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            raise ValueError("PD_ID query missing or ambiguous")
        row = rows[0]
        if (
            str(row.get("pd_id")) != "2839420"
            or row.get("brand_name") != "Samsung"
            or not isinstance(row.get("model_number"), str)
            or not row["model_number"]
        ):
            raise ValueError("PD_ID record identity invalid")
        return {
            key: row.get(key)
            for key in (
                "pd_id",
                "brand_name",
                "model_number",
                "additional_model_information",
                "upc",
                "markets",
                "date_qualified",
                "energy_star_model_identifier",
                "annual_energy_use_kwh_yr",
                "capacity_total_volume_ft3",
            )
        }
    if name == "refrigerator-record-2839420":
        return {
            "content_status": "PRODUCT_TEXT_PRESENT"
            if b"2839420" in body and b"RF23D" in body
            else "SHELL_OR_PRODUCT_TEXT_NOT_OBSERVED"
        }
    return {"content_status": "RAW_DOCUMENT_ONLY_NOT_INTERPRETED"}


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
        if "projection" in record and record["projection"] != project_source(record["name"], raw):
            raise ValueError("Captured source projection does not replay")
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
            try:
                response = urllib.request.urlopen(request, timeout=45)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                body, status, content_type = (
                    response.read(),
                    response.status,
                    response.headers.get("Content-Type", ""),
                )
            (out / (name + ".bin")).write_bytes(body)
            record = source_record(name, url, status, content_type, body)
            records.append(record)
            record["projection"] = project_source(name, body)
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

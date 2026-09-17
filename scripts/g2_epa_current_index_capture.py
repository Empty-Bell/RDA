"""Capture EPA current Model Index and refrigerator row; no certification conclusion."""

import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PD_ID = "2839420"
SOURCES = {
    "model-index-metadata": "https://data.energystar.gov/api/views/8wj2-sec8.json",
    "model-index-row": "https://data.energystar.gov/resource/8wj2-sec8.json?$where=pd_id%3D2839420&$limit=2",
    "refrigerator-row": "https://data.energystar.gov/resource/p5st-her9.json?$where=pd_id%3D2839420&$limit=2",
}
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def project(name: str, body: bytes) -> dict:
    data = json.loads(body)
    if name == "model-index-metadata":
        fields = {
            column.get("fieldName")
            for column in data.get("columns", [])
            if isinstance(column, dict)
        }
        required = {"pd_id", "brand_name", "model_number", "energy_star_model_identifier"}
        if data.get("id") != "8wj2-sec8" or not required <= fields:
            raise ValueError("Model Index schema identity invalid")
        return {"id": data["id"], "rows_updated_at": data.get("rowsUpdatedAt")}
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError("EPA PD_ID query missing or ambiguous")
    row = data[0]
    required = ("pd_id", "brand_name", "model_number", "energy_star_model_identifier")
    if str(row.get("pd_id")) != PD_ID or any(not row.get(key) for key in required[1:]):
        raise ValueError("EPA PD_ID row identity invalid")
    return {key: row.get(key) for key in required + ("markets", "date_certified")}


def validate_cross_source(index: dict, refrigerator: dict) -> dict:
    for key in ("pd_id", "brand_name", "model_number", "energy_star_model_identifier"):
        if index[key] != refrigerator[key]:
            raise ValueError("EPA Model Index and refrigerator row disagree: " + key)
    return {
        "cross_source_key_agreement": "OBSERVED",
        "current_certification_state": "NOT_EVALUATED",
        "assessment": "NOT_EVALUATED",
    }


def source_record(name: str, body: bytes, status: int, content_type: str) -> dict:
    if status != 200 or not body:
        raise ValueError("EPA source unavailable: " + name)
    return {
        "name": name,
        "url": SOURCES[name],
        "status": status,
        "content_type": content_type,
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "size_bytes": len(body),
    }


def replay_capture(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    projections = {}
    for record in manifest["sources"]:
        body = (root / (record["name"] + ".bin")).read_bytes()
        if hashlib.sha256(body).hexdigest() != record["body_sha256"]:
            raise ValueError("EPA current-index source hash does not replay")
        projections[record["name"]] = project(record["name"], body)
    if projections != manifest["projections"]:
        raise ValueError("EPA current-index projection does not replay")
    if (
        validate_cross_source(projections["model-index-row"], projections["refrigerator-row"])
        != manifest["cross_source"]
    ):
        raise ValueError("EPA current-index cross-source result does not replay")
    return manifest


def main() -> None:
    out = Path("runtime/g2-epa-current-index-capture")
    out.mkdir(parents=True, exist_ok=True)
    records, projections = [], {}
    try:
        for name, url in SOURCES.items():
            request = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,*/*;q=0.8"}
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
            records.append(source_record(name, body, status, content_type))
            projections[name] = project(name, body)
        manifest = {
            "contract": "G2_EPA_CURRENT_INDEX_SOURCE_CAPTURE_ONLY_V1",
            "status": "PASS",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "run_id": os.getenv("GITHUB_RUN_ID"),
            "git_sha": os.getenv("GITHUB_SHA"),
            "sources": records,
            "projections": projections,
            "cross_source": validate_cross_source(
                projections["model-index-row"], projections["refrigerator-row"]
            ),
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        replay_capture(out)
    except Exception as error:
        (out / "manifest.json").write_text(
            json.dumps(
                {
                    "contract": "G2_EPA_CURRENT_INDEX_SOURCE_CAPTURE_ONLY_V1",
                    "status": "FAIL",
                    "error": str(error),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise


if __name__ == "__main__":
    main()

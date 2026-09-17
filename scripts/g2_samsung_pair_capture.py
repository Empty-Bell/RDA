"""Capture one Samsung-declared model pair as source observation only."""

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE_NAME = "samsung-rf23db9600qlaa-pdp"
SOURCE_URL = "https://www.samsung.com/us/refrigerators/french-door/bespoke-counter-depth-4-door-flex-refrigerator-23-cu-ft-with-beverage-center-in-stainless-steel-sku-rf23db9600qlaa/"
PAIR_RE = re.compile(rb"RF23DB9600QL\s*/\s*RF23DB9600QLAA")
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def project_declared_pair(body: bytes) -> dict:
    """Extract one literal manufacturer-declared pair; no string derivation."""
    matches = PAIR_RE.findall(body)
    if len(matches) != 1:
        raise ValueError("Samsung declared pair missing or ambiguous")
    raw_field = matches[0].decode("ascii")
    left, right = (part.strip() for part in raw_field.split("/"))
    return {
        "raw_field": raw_field,
        "left_identifier": left,
        "right_identifier": right,
        "observation": "MANUFACTURER_DECLARED_PAIR_ONLY",
        "identity_state": "NOT_EVALUATED",
        "assessment": "NOT_EVALUATED",
    }


def source_record(status: int, content_type: str, body: bytes) -> dict:
    if status != 200 or not body:
        raise ValueError(f"Samsung PDP unavailable ({status})")
    return {
        "name": SOURCE_NAME,
        "url": SOURCE_URL,
        "status": status,
        "content_type": content_type,
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "size_bytes": len(body),
    }


def replay_capture(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    record = manifest["source"]
    body = (root / (record["name"] + ".bin")).read_bytes()
    if hashlib.sha256(body).hexdigest() != record["body_sha256"]:
        raise ValueError("Samsung captured source hash does not replay")
    if manifest["projection"] != project_declared_pair(body):
        raise ValueError("Samsung captured pair projection does not replay")
    return manifest


def main() -> None:
    out = Path("runtime/g2-samsung-pair-capture")
    out.mkdir(parents=True, exist_ok=True)
    try:
        request = urllib.request.Request(
            SOURCE_URL, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8"}
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
        (out / (SOURCE_NAME + ".bin")).write_bytes(body)
        record = source_record(status, content_type, body)
        manifest = {
            "contract": "G2_SAMSUNG_DECLARED_PAIR_SOURCE_CAPTURE_ONLY_V1",
            "status": "PASS",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "run_id": os.getenv("GITHUB_RUN_ID"),
            "git_sha": os.getenv("GITHUB_SHA"),
            "source": record,
            "projection": project_declared_pair(body),
            "epa_identity": "NOT_EVALUATED",
            "ocr_correction": "NOT_APPLIED",
            "assessment": "NOT_EVALUATED",
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        replay_capture(out)
    except Exception as error:
        (out / "manifest.json").write_text(
            json.dumps(
                {
                    "contract": "G2_SAMSUNG_DECLARED_PAIR_SOURCE_CAPTURE_ONLY_V1",
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

"""Capture EPA's disqualified-product XLSX as raw evidence; never parse or match it."""

import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

INTEGRITY_URL = (
    "https://www.energystar.gov/partner-resources/products_partner_resources/products_integrity"
)
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


class _XlsxLinkFinder(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if (
            href
            and ".xlsx" in href.lower()
            and ("disqual" in href.lower() or "dqpl" in href.lower())
        ):
            self.links.append(href)


def discover_xlsx_url(page: bytes, base_url: str = INTEGRITY_URL) -> str:
    """Find exactly one official disqualified-list XLSX link without reading XLSX rows."""
    finder = _XlsxLinkFinder()
    finder.feed(page.decode("utf-8", errors="replace"))
    candidates = sorted({urljoin(base_url, href) for href in finder.links})
    if len(candidates) != 1:
        raise ValueError("EPA disqualified-list XLSX link missing or ambiguous")
    return candidates[0]


def project_source(name: str, body: bytes) -> dict:
    """Validate file/container identity only; retain all list contents unparsed."""
    if name == "integrity-page":
        return {
            "disqualified_list_url": discover_xlsx_url(body),
            "content_state": "RAW_DOCUMENT_ONLY_NOT_INTERPRETED",
        }
    if name == "disqualified-list":
        if not body.startswith(b"PK\x03\x04"):
            raise ValueError("EPA disqualified-list is not an XLSX ZIP container")
        return {"content_state": "XLSX_BYTES_ONLY_NOT_PARSED"}
    raise ValueError("Unknown EPA disqualified source")


def source_record(name: str, requested_url: str, response, body: bytes) -> dict:
    status = response.status
    if status != 200 or not body:
        raise ValueError(f"EPA source unavailable: {name} ({status})")
    return {
        "name": name,
        "requested_url": requested_url,
        "final_url": response.geturl(),
        "status": status,
        "content_type": response.headers.get("Content-Type", ""),
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "size_bytes": len(body),
    }


def fetch(url: str, accept: str):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    try:
        return urllib.request.urlopen(request, timeout=45)
    except urllib.error.HTTPError as error:
        return error


def replay_capture(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    records = {record["name"]: record for record in manifest["sources"]}
    if set(records) != {"integrity-page", "disqualified-list"}:
        raise ValueError("EPA disqualified capture source set invalid")
    projections = {}
    for name, record in records.items():
        body = (root / f"{name}.bin").read_bytes()
        if hashlib.sha256(body).hexdigest() != record["body_sha256"]:
            raise ValueError("EPA disqualified source hash does not replay")
        projections[name] = project_source(name, body)
    if projections != manifest["projections"]:
        raise ValueError("EPA disqualified source projection does not replay")
    if (
        projections["integrity-page"]["disqualified_list_url"]
        != records["disqualified-list"]["requested_url"]
    ):
        raise ValueError("EPA disqualified XLSX URL does not replay from integrity page")
    return manifest


def main() -> None:
    out = Path("runtime/g2-epa-disqualified-capture")
    out.mkdir(parents=True, exist_ok=True)
    records, projections = [], {}
    try:
        with fetch(INTEGRITY_URL, "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8") as response:
            page = response.read()
            record = source_record("integrity-page", INTEGRITY_URL, response, page)
        (out / "integrity-page.bin").write_bytes(page)
        records.append(record)
        projections["integrity-page"] = project_source("integrity-page", page)

        xlsx_url = projections["integrity-page"]["disqualified_list_url"]
        with fetch(
            xlsx_url, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*;q=0.8"
        ) as response:
            xlsx = response.read()
            record = source_record("disqualified-list", xlsx_url, response, xlsx)
        (out / "disqualified-list.bin").write_bytes(xlsx)
        records.append(record)
        projections["disqualified-list"] = project_source("disqualified-list", xlsx)

        manifest = {
            "contract": "G2_EPA_DISQUALIFIED_SOURCE_CAPTURE_ONLY_V1",
            "status": "PASS",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "run_id": os.getenv("GITHUB_RUN_ID"),
            "git_sha": os.getenv("GITHUB_SHA"),
            "sources": records,
            "projections": projections,
            "identity_matching": "NOT_EVALUATED",
            "disqualification_state": "NOT_EVALUATED",
            "assessment": "NOT_EVALUATED",
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        replay_capture(out)
    except Exception as error:
        (out / "manifest.json").write_text(
            json.dumps(
                {
                    "contract": "G2_EPA_DISQUALIFIED_SOURCE_CAPTURE_ONLY_V1",
                    "status": "FAIL",
                    "error": str(error),
                    "sources": records,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise


if __name__ == "__main__":
    main()

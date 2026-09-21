"""Collect per-SKU Energy Star source declarations.

Headless browser sessions transport PF and Bridge JSON. This collector records
source declarations and assessment evidence; it does not inspect rendered logos.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

from source_contract import pdp_facts, pf_population, project_bridge


PF_URL = "https://sribsrch.ecom.samsung.com/estoresearch-api/v1/scom/us/pf_search"
BRIDGE_URL = "https://www.samsung.com/us/gapi/v1/bridge/cacheable/bridge-data"
PLP_URL = "https://www.samsung.com/us/refrigerators/all-refrigerators/"
DESKTOP_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/153.0.8010.12 Safari/537.36"
)
HEADER_PROFILE = "DESKTOP_LINUX_CHROME_153"
GROUP_ID = re.compile(r"^MULTI_GROUP_ID_(\d+)$")
NEXT_DATA = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL
)


def _json(body: bytes, label: str):
    try:
        return json.loads(body)
    except json.JSONDecodeError as error:
        raise ValueError(label + " was not JSON") from error


def extract_next_products(html: bytes) -> list[dict]:
    """Return only the exact SKU and source declaration from PDP Next data."""
    match = NEXT_DATA.search(html.decode("utf-8", "replace"))
    if not match:
        raise ValueError("PDP response has no __NEXT_DATA__ payload")
    data = _json(match.group(1).encode(), "PDP Next payload")
    try:
        products = data["props"]["pageProps"]["productData"]["products"]
    except (KeyError, TypeError) as error:
        raise ValueError("PDP Next productData.products contract changed") from error
    if not isinstance(products, list) or not products:
        raise ValueError("PDP Next productData.products is empty")
    result = []
    seen = set()
    for product in products:
        if not isinstance(product, dict):
            raise ValueError("PDP Next product record is not an object")
        sku = product.get("modelCode")
        if not isinstance(sku, str) or not sku or sku in seen:
            raise ValueError("PDP Next exact SKU is missing or duplicated")
        seen.add(sku)
        result.append({"exact_sku": sku, "pdp_energy_star_flag_raw": product.get("energyStarFlag")})
    return result


def project_group_declarations(group: dict, next_html: bytes, bridge: dict) -> list[dict]:
    """Join source records by exact SKU; representative values are never shared."""
    variants = group.get("groupedProductList")
    if not isinstance(variants, list) or not variants:
        raise ValueError("PF group has no variants")
    pf_by_sku = {}
    for variant in variants:
        sku = variant.get("modelCode") if isinstance(variant, dict) else None
        if not isinstance(sku, str) or not sku or sku in pf_by_sku:
            raise ValueError("PF variant exact SKU is missing or duplicated")
        pf_by_sku[sku] = variant
    next_by_sku = {row["exact_sku"]: row for row in extract_next_products(next_html)}
    if set(next_by_sku) != set(pf_by_sku):
        raise ValueError("PDP Next exact SKU set differs from its PF group")
    rows = []
    for sku in sorted(pf_by_sku):
        facts = pdp_facts(project_bridge(bridge), sku, family="refrigerator")
        rows.append(
            {
                "exact_sku": sku,
                "source_family_id": group["group_id"],
                "representative_sku": group["modelCode"],
                "sku_role": "REPRESENTATIVE" if sku == group["modelCode"] else "VARIANT",
                "pdp_url": urljoin("https://www.samsung.com", pf_by_sku[sku]["pdpURL"]),
                "plp_energy_star_flag_raw": pf_by_sku[sku].get("energyStarFlg"),
                "pdp_energy_star_flag_raw": next_by_sku[sku]["pdp_energy_star_flag_raw"],
                "pdp_energy_star_spec_rows_raw": facts["energy_star_spec_claim_raw"],
            }
        )
    return rows


def project_sku_declaration(group: dict, variant: dict, next_html: bytes, bridge: dict) -> dict:
    """Project one SKU from its own PDP Next and its own Bridge response."""
    sku = variant.get("modelCode")
    if not isinstance(sku, str) or not sku:
        raise ValueError("PF variant exact SKU is missing")
    next_rows = {row["exact_sku"]: row for row in extract_next_products(next_html)}
    if sku not in next_rows:
        raise ValueError("PDP Next response does not declare the requested exact SKU")
    facts = pdp_facts(project_bridge(bridge), sku, family="refrigerator")
    return {
        "exact_sku": sku,
        "source_family_id": group["group_id"],
        "representative_sku": group["modelCode"],
        "sku_role": "REPRESENTATIVE" if sku == group["modelCode"] else "VARIANT",
        "pdp_url": urljoin("https://www.samsung.com", variant["pdpURL"]),
        "plp_energy_star_flag_raw": variant.get("energyStarFlg"),
        "pdp_energy_star_flag_raw": next_rows[sku]["pdp_energy_star_flag_raw"],
        "pdp_energy_star_spec_rows_raw": facts["energy_star_spec_claim_raw"],
    }


def _request(url: str, *, body: bytes | None = None, accept: str) -> tuple[int, str, bytes]:
    headers = {
        "User-Agent": DESKTOP_USER_AGENT,
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": PLP_URL,
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=45)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers.get("Content-Type", ""), response.read()


def _write_raw(root: Path, relative: str, body: bytes) -> dict:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return {"file": relative, "sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body)}


def load_browser_observed_pf(source: Path) -> tuple[list[dict], list[dict]]:
    """Load the current PF API response captured by the existing session collector.

    Samsung rejects an otherwise equivalent unauthenticated PF POST.  This is
    only the current population hand-off; no logo/spec DOM observation is used.
    """
    recon = _json((source / "recon.json").read_bytes(), "PF session manifest")
    if recon.get("status") != "PASS":
        raise ValueError("PF session collector did not pass")
    if os.getenv("GITHUB_RUN_ID") and recon.get("run_id") != os.getenv("GITHUB_RUN_ID"):
        raise ValueError("PF session capture is from another GitHub execution")
    if os.getenv("GITHUB_SHA") and recon.get("git_sha") != os.getenv("GITHUB_SHA"):
        raise ValueError("PF session capture is from another source revision")
    pages, records = {}, {}
    for observation in recon.get("observations", []):
        body = observation.get("request_body")
        fixture = observation.get("fixture")
        if not isinstance(body, dict) or not isinstance(fixture, str):
            continue
        offset = int(body["startIndex"])
        raw = (source / fixture).read_bytes()
        if hashlib.sha256(raw).hexdigest() != observation.get("fixture_sha256"):
            raise ValueError("PF session fixture hash mismatch")
        if offset in pages and pages[offset] != raw:
            raise ValueError("PF session repeated offset changed")
        pages[offset] = raw
        records[offset] = {
            "source_fixture": fixture,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw),
            "url": observation.get("url"),
            "request_body": body,
            "status": observation.get("status"),
        }
    if not pages:
        raise ValueError("PF session collector captured no PF pages")
    return [_json(pages[offset], "PF session page") for offset in sorted(pages)], [records[offset] for offset in sorted(records)]


def capture_session_bridges(products: list[dict], raw: Path) -> tuple[dict[str, dict], dict]:
    """Capture only Specs/Support JSON from Samsung's required browser session.

    The browser is transport for Samsung's session-bound endpoint.  This function
    neither reads the DOM nor applies selectors or visual publication logic.
    """
    from playwright.sync_api import sync_playwright
    from browser_runtime import desktop_context

    captured = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context, identity = desktop_context(browser)
        for number, product in enumerate(products):
            sku = product["exact_sku"]
            page = context.new_page()
            responses = []

            def receive(response):
                parsed = urlsplit(response.url)
                query = parse_qs(parsed.query)
                data_types = set(query.get("data_type", [""])[0].split(","))
                if (
                    parsed.scheme == "https"
                    and parsed.hostname == "www.samsung.com"
                    and parsed.path == "/us/gapi/v1/bridge/cacheable/bridge-data"
                    and "Specs" in data_types
                ):
                    responses.append(response)

            page.on("response", receive)
            try:
                response = page.goto(
                    product["pdp_url"],
                    wait_until="domcontentloaded", timeout=60000,
                )
                if not response or response.status != 200:
                    raise ValueError("PDP session navigation failed")
                for _ in range(10):
                    if responses:
                        break
                    page.wait_for_timeout(1000)
                if not responses:
                    raise ValueError("PDP session did not request a Specs bridge response")
                candidates = []
                observed_sets = []
                for source_response in responses:
                    if source_response.status != 200 or "json" not in source_response.headers.get("content-type", "").lower():
                        continue
                    body = source_response.body()
                    try:
                        bridge = project_bridge(_json(body, "PDP session bridge"))
                        observed_skus = {entry.get("modelCode") for entry in bridge["Specs"]}
                        observed_sets.append(sorted(observed_skus))
                        if sku not in observed_skus:
                            continue
                        pdp_facts(bridge, sku, family="refrigerator")
                    except ValueError:
                        continue
                    candidates.append((source_response, body))
                if not candidates:
                    raise ValueError(
                        "No exact-SKU Specs/Support bridge response; expected="
                        + sku
                        + "; observed="
                        + "|".join(",".join(skus) for skus in observed_sets)
                    )
                if len({hashlib.sha256(body).hexdigest() for _, body in candidates}) != 1:
                    raise ValueError("Multiple nonidentical exact-SKU bridge responses")
                source_response, body = candidates[0]
                record = _write_raw(raw, f"bridge/sku-{number:02d}.json", body)
                record.update({"url": source_response.url, "status": source_response.status})
                captured[sku] = {"body": body, "record": record}
            finally:
                page.close()
        context.close()
        browser.close()
    return captured, identity


def capture(out: Path, run_id: str, *, include_epa: bool, pf_source: Path) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    raw = out / "raw"
    pages, page_records = load_browser_observed_pf(pf_source)
    for number, record in enumerate(page_records):
        fixture = record.pop("source_fixture")
        source_body = (pf_source / fixture).read_bytes()
        record.update(_write_raw(raw, f"pf/page-{number:02d}.json", source_body))
    population = pf_population(pages)
    groups = [group for page in pages for group in page["searchResults"]]
    pf_source_by_sku = {}
    for page, page_source in zip(pages, page_records):
        for group in page["searchResults"]:
            for variant in group["groupedProductList"]:
                pf_source_by_sku[variant["modelCode"]] = {
                    "file": page_source["file"],
                    "url": page_source.get("url"),
                    "sha256": page_source["sha256"],
                    "field": "energyStarFlg",
                    "exact_sku": variant["modelCode"],
                }
    products = []
    for group in groups:
        for variant in group["groupedProductList"]:
            products.append({
                "group": group,
                "variant": variant,
                "exact_sku": variant["modelCode"],
                "pdp_url": urljoin("https://www.samsung.com", variant["pdpURL"]),
                "pf_source_evidence": pf_source_by_sku[variant["modelCode"]],
            })
    session_bridges, session_identity = capture_session_bridges(products, raw)
    declarations, group_records = [], []
    for number, product in enumerate(products):
        group, variant, sku = product["group"], product["variant"], product["exact_sku"]
        session_bridge = session_bridges.get(sku)
        if session_bridge is None:
            raise ValueError("PDP session bridge is missing for exact SKU")
        bridge = _json(session_bridge["body"], "Bridge source")
        bridge_record = session_bridge["record"]
        status, content_type, next_body = _request(product["pdp_url"], accept="text/html,application/xhtml+xml,*/*;q=0.8")
        if status != 200 or "html" not in content_type.lower():
            raise ValueError("PDP Next source unavailable or not HTML")
        next_record = _write_raw(raw, f"next/sku-{number:02d}.html", next_body)
        next_record.update({"url": product["pdp_url"], "status": status})
        declaration = project_sku_declaration(group, variant, next_body, bridge)
        declaration["source_evidence_refs"] = {
            "plp_logo_source": product["pf_source_evidence"],
            "pdp_logo_source": {
                "file": next_record["file"], "url": next_record["url"],
                "sha256": next_record["sha256"], "field": "energyStarFlag",
                "exact_sku": sku,
            },
            "pdp_spec_certification_source": {
                "file": bridge_record["file"], "url": bridge_record["url"],
                "sha256": bridge_record["sha256"],
                "field": "Bridge Specs ENERGY STAR rows", "exact_sku": sku,
                "full_specs_collection": "COMPLETE_EXACT_SKU_SPECS",
            },
        }
        declarations.append(declaration)
        group_records.append({"exact_sku": sku, "source_family_id": group["group_id"], "bridge": bridge_record, "next": next_record})
    if len(declarations) != population["unique_exact_skus"] or len({x["exact_sku"] for x in declarations}) != len(declarations):
        raise ValueError("Exact SKU declaration coverage is incomplete or duplicated")
    result = {
        "contract": "G2_ENERGY_STAR_DIRECT_SOURCE_DECLARATIONS_V1",
        "status": "PASS",
        "scope": "Per-SKU PF, PDP Next, Bridge and EPA Current Index source capture with three-point assessment; no visual inspection",
        "run_id": run_id,
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "git_sha": os.getenv("GITHUB_SHA"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "visual_browser_inspection_used": False,
        "session_transport": "PF_AND_BRIDGE_SESSION_JSON_ONLY",
        "session_browser_identity": session_identity,
        "pf_population_handoff": "CURRENT_PF_API_RESPONSE_FROM_SEPARATE_SESSION_COLLECTOR",
        "header_profile": HEADER_PROFILE,
        "population": {"total_groups": population["total_groups"], "unique_exact_skus": population["unique_exact_skus"], "pf_pages": page_records},
        "groups": group_records,
        "declarations": declarations,
        "rule_evaluation": "NOT_EVALUATED",
    }
    (out / "manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if include_epa:
        epa_out = out / "epa-current-index"
        env = {**os.environ, "RDA_EXECUTION_ID": run_id}
        subprocess.run(
            [sys.executable, str(Path(__file__).with_name("g2_epa_current_index_samsung_capture.py")), "--out", str(epa_out)],
            check=True,
            env=env,
        )
        from g2_energy_star_current_index_binding import bind_current_index
        binding = bind_current_index(result, epa_out)
        (out / "current-index-binding.json").write_text(
            json.dumps(binding, indent=2) + "\n", encoding="utf-8"
        )
        from g2_energy_star_input_review import build_input_review
        review = build_input_review(result["declarations"], binding)
        (out / "three-point-input-review.json").write_text(
            json.dumps(review, indent=2) + "\n", encoding="utf-8"
        )
        from g2_energy_star_assessment import build_assessment
        assessment = build_assessment(
            review,
            expected_exact_skus=population["unique_exact_skus"],
            query_completeness=binding["scan_query_completeness"],
        )
        (out / "energy-star-assessment.json").write_text(
            json.dumps(assessment, indent=2) + "\n", encoding="utf-8"
        )
        from g2_energy_star_review_report import render_review_report
        (out / "energy-star-review.md").write_text(
            render_review_report(assessment), encoding="utf-8"
        )
        result["epa_current_index_manifest"] = "epa-current-index/manifest.json"
        result["current_index_binding"] = "current-index-binding.json"
        result["three_point_input_review"] = "three-point-input-review.json"
        result["energy_star_assessment"] = "energy-star-assessment.json"
        result["energy_star_review_report"] = "energy-star-review.md"
        result["assessment_counts"] = assessment["counts"]
        result["rule_evaluation"] = "COMPLETED_FOR_SOURCE_CAPTURE"
        (out / "manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("runtime/g2-energy-star-source") / uuid.uuid4().hex)
    parser.add_argument("--skip-epa", action="store_true")
    parser.add_argument("--pf-source", type=Path, required=True)
    args = parser.parse_args()
    run_id = os.getenv("RDA_EXECUTION_ID", uuid.uuid4().hex)
    try:
        capture(args.out, run_id, include_epa=not args.skip_epa, pf_source=args.pf_source)
    except Exception as error:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "manifest.json").write_text(json.dumps({"status": "FAIL", "error": str(error), "run_id": run_id}, indent=2) + "\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    main()

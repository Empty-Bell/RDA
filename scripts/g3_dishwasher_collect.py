"""Collect exact dishwasher SKU PDP facts from a completed source artifact."""

from datetime import datetime, timezone
import hashlib
import argparse
import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote, urljoin, urlsplit

from regaudit.population import canonicalize_products
from source_contract import pf_population, pdp_facts, project_bridge
from runner_probe import safe_url
from browser_runtime import desktop_context
from claim_recon import DOM_SNAPSHOT, claim_facts, project_inline_product_claims


CONTRACT = "G3_DISHWASHER_EXACT_SKU_PDP_V1"
PLP_URL = "https://www.samsung.com/us/dishwashers/all-dishwashers/"


def _json(path: Path) -> Any:
    return json.loads(path.read_bytes())


def load_population(recon_root: str | Path, source_run_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = Path(recon_root)
    recon = _json(root / "recon.json")
    if recon.get("status") != "PASS" or recon.get("run_id") != str(source_run_id):
        raise ValueError("Dishwasher source artifact is not the requested successful run")
    if recon.get("scope") != "dishwasher source contracts only":
        raise ValueError("Source artifact is not scoped to dishwasher")
    pages_by_offset: dict[int, tuple[dict[str, Any], str]] = {}
    for observation in recon.get("observations", []):
        request = observation.get("request_body")
        fixture = observation.get("fixture")
        if not isinstance(request, dict) or not isinstance(fixture, str):
            continue
        path = root / fixture
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != observation.get("fixture_sha256"):
            raise ValueError("Dishwasher PF fixture hash mismatch")
        offset = int(request["startIndex"])
        page = json.loads(raw)
        if offset in pages_by_offset and pages_by_offset[offset][0] != page:
            raise ValueError("Dishwasher PF offset changed inside the source artifact")
        pages_by_offset[offset] = (page, digest)
    if not pages_by_offset:
        raise ValueError("Dishwasher source artifact has no PF pages")
    ordered = sorted(pages_by_offset)
    pages = [pages_by_offset[offset][0] for offset in ordered]
    population = pf_population(pages)
    products = []
    claim_listings: dict[str, dict[str, Any]] = {}
    for offset in ordered:
        page = pages_by_offset[offset][0]
        digest = pages_by_offset[offset][1]
        for group in page["searchResults"]:
            for variant in group["groupedProductList"]:
                sku = variant["modelCode"]
                claim_listings[sku] = {key: variant.get(key) for key in ("modelCode", "modelName", "ecomFlag", "stockFlag", "energyStarFlg")}
                products.append({"run_id": source_run_id, "exact_sku": sku, "listings": [{
                    "product_group": "dishwasher",
                    "source_family_id": group["group_id"],
                    "representative_sku": group["modelCode"],
                    "sku_role": "REPRESENTATIVE" if sku == group["modelCode"] else "VARIANT",
                    "plp_url": PLP_URL,
                    "pdp_url": urljoin("https://www.samsung.com", variant["pdpURL"]),
                    "source_pf_search_hash": digest,
                    "source_family_code": {"state": "NOT_OBSERVED", "value": None, "error": None},
                    "commerce_status": {"state": "NOT_OBSERVED", "value": None, "error": None},
                    "stock_flag": {"state": "NOT_OBSERVED", "value": None, "error": None},
                    "ecom_flag": {"state": "VALUE" if variant.get("ecomFlag") is not None else "NOT_OBSERVED",
                                  "value": variant.get("ecomFlag"), "error": None},
                    "variant_attributes": {"state": "NOT_OBSERVED", "value": None, "error": None},
                }]})
    canonical = canonicalize_products(products)
    for product in canonical:
        product["source_claim_listing_raw"] = claim_listings[product["exact_sku"]]
    if len(canonical) != population["unique_exact_skus"]:
        raise ValueError("Dishwasher exact SKU population projection changed cardinality")
    return canonical, {"source_run_id": source_run_id, "total_groups": population["total_groups"],
                       "unique_exact_skus": population["unique_exact_skus"],
                       "pf_page_count": len(pages), "pf_page_hashes": [pages_by_offset[i][1] for i in ordered]}


def verify_identity(sku: str, final_url: str, snapshot: dict[str, Any], bridge: dict[str, Any]) -> dict[str, Any]:
    parts = urlsplit(final_url)
    slug = re.escape(sku.lower().replace("/", "-"))
    if parts.scheme != "https" or parts.hostname != "www.samsung.com" or "/us/" not in parts.path or not re.search(r"-sku-" + slug + r"/?$", parts.path.lower()):
        raise ValueError("Final dishwasher PDP URL refers to another exact SKU")
    if snapshot.get("jsonld_parse_errors"):
        raise ValueError("Dishwasher PDP JSON-LD parse failed")
    declarations = snapshot.get("product_jsonld")
    if not isinstance(declarations, list) or not declarations:
        raise ValueError("Dishwasher PDP has no current Product JSON-LD identity")
    for declaration in declarations:
        identities = [declaration[key] for key in ("sku", "mpn") if declaration.get(key)]
        if not identities or any(value != sku for value in identities):
            raise ValueError("Dishwasher PDP JSON-LD does not match exact SKU")
    return pdp_facts(bridge, sku, family="dishwasher")


def prepare_output(output: str | Path) -> Path:
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "pdp").mkdir(exist_ok=True)
    return destination


def sku_directory_name(sku: str) -> str:
    return quote(sku, safe="")


def collect(products: list[dict[str, Any]], output: str | Path) -> list[dict[str, Any]]:
    from playwright.sync_api import sync_playwright

    destination = prepare_output(output)
    pdp_root = destination / "pdp"
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context, identity = desktop_context(browser)
        for index, product in enumerate(products):
            sku = product["exact_sku"]
            folder = pdp_root / sku_directory_name(sku)
            folder.mkdir(exist_ok=False)
            record: dict[str, Any] = {"exact_sku": sku, "status": "FAILED", "browser_identity": identity,
                                      "requested_url": product["listings"][0]["pdp_url"], "bridge_responses": []}
            page = context.new_page()

            def on_response(response: Any) -> None:
                from urllib.parse import parse_qs
                query = parse_qs(urlsplit(response.url).query)
                if not urlsplit(response.url).path.endswith("/bridge-data") or "Specs" not in query.get("data_type", [""])[0].split(","):
                    return
                entry = {"url": safe_url(response.url), "status": response.status,
                         "captured_at": datetime.now(timezone.utc).isoformat()}
                record["bridge_responses"].append(entry)
                try:
                    if len(record["bridge_responses"]) > 8:
                        raise ValueError("Dishwasher bridge response limit exceeded")
                    if response.status != 200 or "json" not in response.headers.get("content-type", "").lower():
                        raise ValueError("Dishwasher bridge response is unavailable or not JSON")
                    projected = project_bridge(response.json())
                    raw = (json.dumps(projected, sort_keys=True, indent=2) + "\n").encode()
                    path = folder / f"bridge-{len(record['bridge_responses'])}.json"
                    path.write_bytes(raw)
                    entry.update(path=path.name, sha256=hashlib.sha256(raw).hexdigest())
                except Exception as error:
                    entry["error_class"] = type(error).__name__

            page.on("response", on_response)
            try:
                response = page.goto(record["requested_url"], wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(8000)
                # Opening Specs prompts Samsung to load the selected model's current bridge payload.
                try:
                    specs = page.get_by_role("button", name=re.compile(r"^Specs$", re.I))
                    if specs.count() == 1:
                        specs.click(timeout=5000)
                        page.wait_for_timeout(1000)
                except Exception:
                    pass
                structured_probes = []
                structured_errors = []
                inline_scripts = page.locator("script#__NEXT_DATA__").all_text_contents()
                for inline in inline_scripts:
                    try:
                        structured_probes.append({**project_inline_product_claims(json.loads(inline)),
                                                  "source_url": safe_url(page.url),
                                                  "source_kind": "public inline NEXT_DATA product array"})
                    except Exception as error:
                        structured_errors.append({"error_type": type(error).__name__})
                snapshot = {"target_sku": sku, **page.evaluate(DOM_SNAPSHOT),
                            "structured_records": [], "structured_probes": structured_probes,
                            "structured_errors": structured_errors,
                            "inline_product_script_count": len(inline_scripts)}
                raw_snapshot = (json.dumps(snapshot, sort_keys=True, indent=2) + "\n").encode()
                (folder / "snapshot.json").write_bytes(raw_snapshot)
                record.update(final_url=safe_url(page.url), http_status=response.status if response else None,
                              snapshot_sha256=hashlib.sha256(raw_snapshot).hexdigest())
                if response is None or response.status != 200:
                    raise ValueError("Dishwasher PDP HTTP request failed")
                if sku.lower() not in page.locator("body").inner_text().lower():
                    raise ValueError("Exact dishwasher SKU is absent from rendered PDP text")
                candidates = []
                for entry in record["bridge_responses"]:
                    if not entry.get("path"):
                        continue
                    bridge = _json(folder / entry["path"])
                    try:
                        facts = verify_identity(sku, page.url, snapshot, bridge)
                    except ValueError:
                        continue
                    candidates.append((entry, facts))
                if not candidates:
                    raise ValueError("No same-SKU URL, JSON-LD, Specs and Support evidence")
                if len({item[0]["sha256"] for item in candidates}) != 1:
                    raise ValueError("Dishwasher bridge changed during same-PDP collection")
                bridge_entry, facts = candidates[0]
                listing_raw = product.get("source_claim_listing_raw")
                if not isinstance(listing_raw, dict):
                    raise ValueError("Dishwasher PF claim declaration is unavailable")
                claim_sources = claim_facts(snapshot, sku, listing_raw, facts)
                record.update(status="VERIFIED_EXACT_IDENTITY", bridge=bridge_entry, pdp_facts_raw=facts,
                              energy_star_claim_sources_raw=claim_sources,
                              identity_contract="FINAL_URL_AND_CURRENT_JSONLD_AND_EXACT_SPECS_SUPPORT")
            except Exception as error:
                record["error"] = str(error).splitlines()[0][:300]
            finally:
                page.close()
                (folder / "result.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            results.append(record)
        context.close()
        browser.close()
    return results


def coverage(products: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    population = {product["exact_sku"] for product in products}
    result_skus = [result.get("exact_sku") for result in results]
    if len(population) != len(products) or len(result_skus) != len(set(result_skus)) or not set(result_skus) <= population:
        raise ValueError("Dishwasher PDP result identities are duplicate or outside population")
    by_sku = {result["exact_sku"]: result.get("status") for result in results}
    if any(status not in ("VERIFIED_EXACT_IDENTITY", "FAILED") for status in by_sku.values()):
        raise ValueError("Dishwasher PDP result status is invalid")
    result_by_sku = {result["exact_sku"]: result for result in results}
    rows = [{"exact_sku": sku, "status": by_sku.get(sku, "NOT_ATTEMPTED"),
             **({"error": result_by_sku[sku].get("error")} if by_sku.get(sku) == "FAILED" else {})}
            for sku in sorted(population)]
    counts = {status: sum(row["status"] == status for row in rows)
              for status in ("VERIFIED_EXACT_IDENTITY", "FAILED", "NOT_ATTEMPTED")}
    return {"population_count": len(population), "attempted_count": len(results),
            "counts": counts, "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recon-root", required=True, help="Extracted G3 dishwasher source artifact directory")
    parser.add_argument("--source-run-id", required=True, help="GitHub Actions ID for the source artifact")
    parser.add_argument("--out", required=True, help="Output directory for exact-SKU PDP evidence")
    args = parser.parse_args()
    products, population = load_population(args.recon_root, args.source_run_id)
    destination = Path(args.out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "population.json").write_text(json.dumps(population, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (destination / "products.json").write_text(json.dumps(products, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    results = collect(products, destination)
    result_coverage = coverage(products, results)
    report = {"contract": CONTRACT, "source_run_id": args.source_run_id,
              "collection_run_id": os.getenv("GITHUB_RUN_ID"), "git_sha": os.getenv("GITHUB_SHA"),
              "captured_at": datetime.now(timezone.utc).isoformat(), "scope": "Dishwasher exact-SKU PDP identity and source facts only",
              "assessment": "NOT_EVALUATED", "population": population, "coverage": result_coverage,
              "status": "PASS" if result_coverage["counts"]["FAILED"] == 0 and result_coverage["counts"]["NOT_ATTEMPTED"] == 0 else "FAILED"}
    (destination / "collection-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        failed_rows = [row for row in result_coverage["rows"] if row["status"] == "FAILED"]
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Dishwasher exact-SKU PDP collection\n\n")
            stream.write(f"Status: **{report['status']}**; population: {result_coverage['population_count']}\n\n")
            stream.write(f"Coverage: `{json.dumps(result_coverage['counts'], sort_keys=True)}`\n\n")
            for row in failed_rows:
                stream.write(f"- `{row['exact_sku']}`: {row.get('error') or 'unknown collection failure'}\n")
    print(json.dumps({"status": report["status"], "population_count": result_coverage["population_count"],
                      "coverage_counts": result_coverage["counts"]}, sort_keys=True), flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

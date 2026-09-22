"""Collect exact-SKU dryer PDP facts from a successful source artifact."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote, urljoin, urlsplit

from regaudit.population import canonicalize_products
from source_contract import pf_population, pdp_facts, project_bridge
from runner_probe import safe_url
from browser_runtime import desktop_context
from claim_recon import DOM_SNAPSHOT, claim_facts, project_inline_product_claims


PLP_URL = "https://www.samsung.com/us/laundry/dryers/"
CONTRACT = "G3_DRYER_EXACT_SKU_PDP_V1"


def load_json(path):
    return json.loads(Path(path).read_bytes())


def load_population(recon_root, source_run_id):
    root = Path(recon_root)
    recon = load_json(root / "recon.json")
    if recon.get("status") != "PASS" or str(recon.get("run_id")) != str(source_run_id):
        raise ValueError("Dryer source artifact is not the requested successful run")
    if recon.get("scope") != "dryer source contracts only":
        raise ValueError("Source artifact is not scoped to clothes dryers")
    pages_by_offset = {}
    for observation in recon.get("observations", []):
        request, fixture = observation.get("request_body"), observation.get("fixture")
        if not isinstance(request, dict) or not isinstance(fixture, str):
            continue
        raw = (root / fixture).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != observation.get("fixture_sha256"):
            raise ValueError("Dryer PF fixture hash mismatch")
        offset = int(request["startIndex"])
        page = json.loads(raw)
        if offset in pages_by_offset and pages_by_offset[offset][0] != page:
            raise ValueError("Dryer PF offset changed within source artifact")
        pages_by_offset[offset] = (page, digest)
    if not pages_by_offset:
        raise ValueError("Dryer source artifact has no PF pages")
    offsets = sorted(pages_by_offset)
    pages = [pages_by_offset[offset][0] for offset in offsets]
    population = pf_population(pages)
    products, listing_by_sku = [], {}
    for offset in offsets:
        page, digest = pages_by_offset[offset]
        for group in page["searchResults"]:
            for variant in group["groupedProductList"]:
                sku = variant["modelCode"]
                listing_by_sku[sku] = {key: variant.get(key) for key in
                                       ("modelCode", "modelName", "ecomFlag", "stockFlag", "energyStarFlg")}
                products.append({"run_id": source_run_id, "exact_sku": sku, "listings": [{
                    "product_group": "dryer", "source_family_id": group["group_id"],
                    "representative_sku": group["modelCode"],
                    "sku_role": "REPRESENTATIVE" if sku == group["modelCode"] else "VARIANT",
                    "plp_url": PLP_URL, "pdp_url": urljoin("https://www.samsung.com", variant["pdpURL"]),
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
        product["source_claim_listing_raw"] = listing_by_sku[product["exact_sku"]]
    if len(canonical) != population["unique_exact_skus"]:
        raise ValueError("Dryer exact-SKU population cardinality changed")
    return canonical, {"source_run_id": str(source_run_id), "total_groups": population["total_groups"],
                       "unique_exact_skus": population["unique_exact_skus"], "pf_page_count": len(pages),
                       "pf_page_hashes": [pages_by_offset[offset][1] for offset in offsets]}


def verify_identity(sku, final_url, snapshot, bridge):
    parts = urlsplit(final_url)
    slug = re.escape(sku.lower().replace("/", "-"))
    if parts.scheme != "https" or parts.hostname != "www.samsung.com" or "/us/" not in parts.path or not re.search(r"-sku-" + slug + r"/?$", parts.path.lower()):
        raise ValueError("Final dryer PDP URL refers to another exact SKU")
    if snapshot.get("jsonld_parse_errors"):
        raise ValueError("Dryer PDP JSON-LD parse failed")
    declarations = snapshot.get("product_jsonld")
    if not isinstance(declarations, list) or not declarations:
        raise ValueError("Dryer PDP has no current Product JSON-LD identity")
    for declaration in declarations:
        identities = [declaration[key] for key in ("sku", "mpn") if declaration.get(key)]
        if not identities or any(value != sku for value in identities):
            raise ValueError("Dryer PDP JSON-LD does not match exact SKU")
    return pdp_facts(bridge, sku, family="dryer")


def collect(products, output):
    from playwright.sync_api import sync_playwright
    destination = Path(output)
    pdp_root = destination / "pdp"
    pdp_root.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context, identity = desktop_context(browser)
        for product in products:
            sku = product["exact_sku"]
            folder = pdp_root / quote(sku, safe="")
            folder.mkdir(exist_ok=False)
            record = {"exact_sku": sku, "status": "FAILED", "browser_identity": identity,
                      "requested_url": product["listings"][0]["pdp_url"], "bridge_responses": []}
            page = context.new_page()

            def on_response(response):
                from urllib.parse import parse_qs
                query = parse_qs(urlsplit(response.url).query)
                if not urlsplit(response.url).path.endswith("/bridge-data") or "Specs" not in query.get("data_type", [""])[0].split(","):
                    return
                entry = {"url": safe_url(response.url), "status": response.status,
                         "captured_at": datetime.now(timezone.utc).isoformat()}
                record["bridge_responses"].append(entry)
                try:
                    if len(record["bridge_responses"]) > 8:
                        raise ValueError("Dryer bridge response limit exceeded")
                    if response.status != 200 or "json" not in response.headers.get("content-type", "").lower():
                        raise ValueError("Dryer bridge response unavailable or not JSON")
                    raw = (json.dumps(project_bridge(response.json()),
                                      sort_keys=True, indent=2) + "\n").encode()
                    path = folder / f"bridge-{len(record['bridge_responses'])}.json"
                    path.write_bytes(raw)
                    entry.update(path=path.name, sha256=hashlib.sha256(raw).hexdigest())
                except Exception as error:
                    entry["error_class"] = type(error).__name__

            page.on("response", on_response)
            try:
                response = page.goto(record["requested_url"], wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(8000)
                try:
                    specs = page.get_by_role("button", name=re.compile(r"^Specs$", re.I))
                    if specs.count() == 1:
                        specs.click(timeout=5000)
                        page.wait_for_timeout(1000)
                except Exception:
                    pass
                probes, errors = [], []
                inline_scripts = page.locator("script#__NEXT_DATA__").all_text_contents()
                for inline in inline_scripts:
                    try:
                        probes.append({**project_inline_product_claims(json.loads(inline)),
                                       "source_url": safe_url(page.url),
                                       "source_kind": "public inline NEXT_DATA product array"})
                    except Exception as error:
                        errors.append({"error_type": type(error).__name__})
                snapshot = {"target_sku": sku, **page.evaluate(DOM_SNAPSHOT), "structured_records": [],
                            "structured_probes": probes, "structured_errors": errors,
                            "inline_product_script_count": len(inline_scripts)}
                raw_snapshot = (json.dumps(snapshot, sort_keys=True, indent=2) + "\n").encode()
                (folder / "snapshot.json").write_bytes(raw_snapshot)
                record.update(final_url=safe_url(page.url), http_status=response.status if response else None,
                              snapshot_sha256=hashlib.sha256(raw_snapshot).hexdigest())
                if response is None or response.status != 200:
                    raise ValueError("Dryer PDP HTTP request failed")
                if sku.lower() not in page.locator("body").inner_text().lower():
                    raise ValueError("Exact dryer SKU is absent from rendered PDP text")
                candidates = []
                for entry in record["bridge_responses"]:
                    if not entry.get("path"):
                        continue
                    bridge = load_json(folder / entry["path"])
                    try:
                        facts = verify_identity(sku, page.url, snapshot, bridge)
                    except ValueError:
                        continue
                    candidates.append((entry, facts))
                if not candidates:
                    raise ValueError("No same-SKU URL, JSON-LD, Specs and Support evidence")
                if len({candidate[0]["sha256"] for candidate in candidates}) != 1:
                    raise ValueError("Dryer bridge changed during same-PDP collection")
                bridge_entry, facts = candidates[0]
                listing = product.get("source_claim_listing_raw")
                if not isinstance(listing, dict):
                    raise ValueError("Dryer PF claim declaration is unavailable")
                claims = claim_facts(snapshot, sku, listing, facts)
                record.update(status="VERIFIED_EXACT_IDENTITY", bridge=bridge_entry, pdp_facts_raw=facts,
                              energy_star_claim_sources_raw=claims,
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


def coverage(products, results):
    population = {product["exact_sku"] for product in products}
    sku_list = [result.get("exact_sku") for result in results]
    if len(population) != len(products) or len(sku_list) != len(set(sku_list)) or not set(sku_list) <= population:
        raise ValueError("Dryer PDP result identities are duplicate or outside population")
    by_sku = {result["exact_sku"]: result.get("status") for result in results}
    if any(status not in ("VERIFIED_EXACT_IDENTITY", "FAILED") for status in by_sku.values()):
        raise ValueError("Dryer PDP result status is invalid")
    result_by_sku = {result["exact_sku"]: result for result in results}
    rows = [{"exact_sku": sku, "status": by_sku.get(sku, "NOT_ATTEMPTED"),
             **({"error": result_by_sku[sku].get("error")} if by_sku.get(sku) == "FAILED" else {})}
            for sku in sorted(population)]
    counts = {state: sum(row["status"] == state for row in rows)
              for state in ("VERIFIED_EXACT_IDENTITY", "FAILED", "NOT_ATTEMPTED")}
    return {"population_count": len(population), "attempted_count": len(results), "counts": counts, "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recon-root", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    products, population = load_population(args.recon_root, args.source_run_id)
    destination = Path(args.out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "population.json").write_text(json.dumps(population, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (destination / "products.json").write_text(json.dumps(products, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = coverage(products, collect(products, destination))
    status = "PASS" if rows["counts"]["FAILED"] == 0 and rows["counts"]["NOT_ATTEMPTED"] == 0 else "FAILED"
    report = {"contract": CONTRACT, "source_run_id": str(args.source_run_id),
              "collection_run_id": os.getenv("GITHUB_RUN_ID"), "git_sha": os.getenv("GITHUB_SHA"),
              "captured_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Dryer exact-SKU PDP identity and source facts only; no combo routing, matching or assessment",
              "assessment": "NOT_EVALUATED", "population": population, "coverage": rows,
              "energyguide_audit": "OUT_OF_SCOPE_FOR_DRYER", "status": status}
    (destination / "collection-summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("## Clothes dryer exact-SKU PDP collection\n\n")
            stream.write(f"Status: **{status}**; population: {rows['population_count']}\n\n")
            stream.write(f"Coverage: `{json.dumps(rows['counts'], sort_keys=True)}`\n\n")
            stream.write("FTC EnergyGuide collection, OCR, and comparison are outside the Clothes Dryer audit scope.\n\n")
            for row in rows["rows"]:
                if row["status"] == "FAILED":
                    stream.write(f"- `{row['exact_sku']}`: {row.get('error', 'collection failure')}\n")
    print(json.dumps({"status": status, "population_count": rows["population_count"],
                      "coverage_counts": rows["counts"]}, sort_keys=True), flush=True)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

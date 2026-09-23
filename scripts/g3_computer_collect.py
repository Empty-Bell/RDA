"""Collect the exact-SKU Samsung Computer PDP population in deterministic shards."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import parse_qs, quote, urlencode, urlsplit

from claim_recon import DOM_SNAPSHOT, claim_facts
from source_contract import computer_selection, pdp_facts, pf_population, project_computer_specs
from browser_runtime import desktop_context
from runner_probe import safe_url

CONTRACT = "G3_COMPUTER_EXACT_SKU_PDP_V1"
PLP_URLS = {
    "computer": "https://www.samsung.com/us/computers/galaxy-book/",
    "chromebook": "https://www.samsung.com/us/computers/chromebook/",
}
SCOPES = {"computer": "computer source contracts only", "chromebook": "chromebook source contracts only"}


def read_json(path):
    return json.loads(Path(path).read_bytes())


def load_leg(root, family, run_id):
    root = Path(root)
    recon = read_json(root / "recon.json")
    checks = recon.get("checks") if isinstance(recon.get("checks"), list) else []
    if (recon.get("status") != "PASS" or str(recon.get("run_id")) != str(run_id)
            or recon.get("scope") != SCOPES[family] or not checks
            or any(not isinstance(row, dict) or row.get("status") != "PASS" for row in checks)):
        raise ValueError(f"Computer {family} source artifact is not the requested successful run")
    pages = {}
    for observation in recon.get("observations", []):
        request, fixture = observation.get("request_body"), observation.get("fixture")
        if not isinstance(request, dict) or not isinstance(fixture, str):
            continue
        raw = (root / fixture).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != observation.get("fixture_sha256"):
            raise ValueError(f"Computer {family} PF fixture hash mismatch")
        offset = int(request["startIndex"])
        page = json.loads(raw)
        if offset in pages and pages[offset][0] != page:
            raise ValueError(f"Computer {family} PF page changed at the same offset")
        pages[offset] = (page, digest)
    if not pages:
        raise ValueError(f"Computer {family} source artifact contains no PF pages")
    offsets = sorted(pages)
    population = pf_population([pages[offset][0] for offset in offsets])
    products = []
    for offset in offsets:
        page, digest = pages[offset]
        for group in page["searchResults"]:
            for variant in group["groupedProductList"]:
                sku = variant["modelCode"]
                products.append({
                    "run_id": str(run_id), "source_leg": family, "exact_sku": sku,
                    "source_claim_listing_raw": {key: variant.get(key) for key in
                        ("modelCode", "modelName", "ecomFlag", "stockFlag", "energyStarFlg")},
                    "listing": {"product_group": family, "source_family_id": group["group_id"],
                        "representative_sku": group["modelCode"],
                        "sku_role": "REPRESENTATIVE" if sku == group["modelCode"] else "VARIANT",
                        "plp_url": PLP_URLS[family], "pdp_url": "https://www.samsung.com" + variant["pdpURL"],
                        "source_pf_search_hash": digest},
                })
    if len(products) != population["unique_exact_skus"]:
        raise ValueError(f"Computer {family} exact-SKU population cardinality changed")
    return products, {"family": family, "source_run_id": str(run_id),
        "group_count": population["total_groups"], "sku_count": len(products),
        "pf_page_count": len(offsets), "pf_page_hashes": [pages[offset][1] for offset in offsets]}


def load_population(computer_root, chromebook_root, run_id):
    book, book_meta = load_leg(computer_root, "computer", run_id)
    chrome, chrome_meta = load_leg(chromebook_root, "chromebook", run_id)
    products = book + chrome
    skus = [row["exact_sku"] for row in products]
    if len(skus) != len(set(skus)):
        raise ValueError("Computer and Chromebook listings overlap or duplicate exact SKUs")
    if len(book) != 23 or len(chrome) != 1 or len(products) != 24:
        raise ValueError("Computer recon population changed; review source scope before collection")
    return products, {"source_run_id": str(run_id), "unique_exact_skus": len(products),
        "source_legs": [book_meta, chrome_meta], "membership": "Galaxy Book plus separately listed Chromebook; exact SKU union"}


def shard_for(sku, count):
    return int.from_bytes(hashlib.sha256(sku.encode("utf-8")).digest()[:4], "big") % count


def collect(products, output):
    from playwright.sync_api import sync_playwright
    destination = Path(output)
    pdp_root = destination / "pdp"
    pdp_root.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context, browser_identity = desktop_context(browser)
        for product in products:
            sku = product["exact_sku"]
            folder = pdp_root / quote(sku, safe="")
            folder.mkdir(parents=True, exist_ok=False)
            record = {"exact_sku": sku, "source_leg": product["source_leg"], "status": "FAILED",
                "requested_url": product["listing"]["pdp_url"], "browser_identity": browser_identity,
                "observed_ecom_group_ids": [], "captured_at": datetime.now(timezone.utc).isoformat()}
            page = context.new_page()
            group_ids = []
            def observe(response):
                parsed = urlsplit(response.url)
                if (parsed.hostname == "www.samsung.com" and parsed.path.endswith("/ecom-data")
                        and response.request.resource_type in ("xhr", "fetch")):
                    group_ids.extend(parse_qs(parsed.query).get("group_id", []))
            page.on("response", observe)
            try:
                response = page.goto(record["requested_url"], wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(10000)
                page.locator('[data-modelcode][aria-checked="true"]').first.wait_for(state="visible", timeout=30000)
                purchase = page.get_by_role("button", name=re.compile(r"^Continue")).first
                selection = {"selected_controls": page.locator('[data-modelcode][aria-checked="true"]').evaluate_all(
                    '(els) => els.map(e => ({sku:e.getAttribute("data-modelcode"),label:e.getAttribute("aria-label")}))'),
                    "continue_sku": purchase.get_attribute("data-modelcode") if purchase.count() else None,
                    "continue_visible": purchase.is_visible() if purchase.count() else False}
                selection_facts = computer_selection(selection, sku)
                final = urlsplit(page.url)
                slug = re.escape(sku.lower().replace("/", "-"))
                if (response is None or response.status != 200 or final.scheme != "https"
                        or final.hostname != "www.samsung.com" or "/us/" not in final.path
                        or not re.search(r"-sku-" + slug + r"/?$", final.path.lower())):
                    raise ValueError("Computer PDP response or final exact-SKU URL is invalid")
                unique_groups = sorted(set(group_ids))
                if len(unique_groups) != 1:
                    raise ValueError("Current PDP did not expose one unambiguous ecom-data group_id")
                record["observed_ecom_group_ids"] = unique_groups
                spec_url = "https://www.samsung.com/us/gapi/v1/bridge/cacheable/bridge-data?" + urlencode({
                    "data_type": "Specs", "store_type": "B2C", "group_id": unique_groups[0],
                    "modelCode": sku, "version": "v2"})
                spec_response = context.request.get(spec_url, timeout=30000)
                if spec_response.status != 200:
                    raise ValueError("Same-page computer Specs endpoint did not return HTTP 200")
                projected = project_computer_specs(spec_response.json())
                facts = pdp_facts(projected, sku, family="computer")
                snapshot = {"target_sku": sku, **page.evaluate(DOM_SNAPSHOT),
                    "structured_records": [], "structured_probes": [], "structured_errors": []}
                if snapshot.get("pdp_logo_selector_contract") != "PDP_ENERGY_STAR_GALLERY_OR_CONFIGURATOR_V3":
                    raise ValueError("Computer PDP logo snapshot contract is missing or stale")
                snapshot_raw = (json.dumps(snapshot, sort_keys=True, indent=2) + "\n").encode()
                (folder / "snapshot.json").write_bytes(snapshot_raw)
                bridge_raw = (json.dumps(projected, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
                (folder / "specs.json").write_bytes(bridge_raw)
                claims = claim_facts(snapshot, sku, product["source_claim_listing_raw"], facts)
                record.update(status="VERIFIED_EXACT_IDENTITY", final_url=safe_url(page.url),
                    selection_identity=selection_facts, selected_configuration_raw=selection, specs_url=safe_url(spec_url),
                    specs_sha256=hashlib.sha256(bridge_raw).hexdigest(),
                    snapshot_sha256=hashlib.sha256(snapshot_raw).hexdigest(),
                    pdp_facts_raw=facts, energy_star_claim_sources_raw=claims,
                    identity_contract="SELECTED_CONFIG_CONTINUE_SKU_CURRENT_ECOM_GROUP_AND_EXACT_SPECS")
            except Exception as error:
                record["error"] = str(error).splitlines()[0][:300]
            finally:
                page.close()
                (folder / "result.json").write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            results.append(record)
        context.close()
        browser.close()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--computer-recon", required=True)
    parser.add_argument("--chromebook-recon", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.shard_count != 3 or not 0 <= args.shard_index < args.shard_count:
        raise ValueError("Computer collection requires one of exactly three deterministic shards")
    products, population = load_population(args.computer_recon, args.chromebook_recon, args.source_run_id)
    selected = [row for row in products if shard_for(row["exact_sku"], args.shard_count) == args.shard_index]
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "population.json").write_text(json.dumps(population, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "products.json").write_text(json.dumps(selected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    results = collect(selected, out)
    statuses = {row["exact_sku"]: row["status"] for row in results}
    if len(statuses) != len(selected) or set(statuses) != {row["exact_sku"] for row in selected}:
        raise ValueError("Computer shard result coverage does not match its assigned SKUs")
    summary = {"contract": CONTRACT, "source_run_id": str(args.source_run_id),
        "collection_run_id": os.getenv("GITHUB_RUN_ID"), "shard_index": args.shard_index,
        "shard_count": args.shard_count, "population_count": len(selected),
        "all_population_skus": sorted(row["exact_sku"] for row in products),
        "assigned_skus": sorted(statuses),
        "coverage_counts": {state: sum(value == state for value in statuses.values())
            for state in ("VERIFIED_EXACT_IDENTITY", "FAILED")},
        "rows": results, "status": "PASS" if all(value == "VERIFIED_EXACT_IDENTITY" for value in statuses.values()) else "FAILED"}
    (out / "shard-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("status", "source_run_id", "shard_index", "shard_count", "population_count", "coverage_counts")}, sort_keys=True), flush=True)
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())


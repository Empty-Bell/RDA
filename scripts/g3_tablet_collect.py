"""Collect exact-SKU Tablet PDP and publication evidence in deterministic shards."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlsplit

from browser_runtime import desktop_context
from claim_recon import DOM_SNAPSHOT, claim_facts
from runner_probe import safe_url
from source_contract import pdp_facts, pf_population, project_computer_specs

CONTRACT = "G3_TABLET_EXACT_SKU_PDP_V1"
SCOPE = "tablet source contracts only"
PLP_URL = "https://www.samsung.com/us/tablets/all-tablets/"
SHARD_COUNT = 4


def read_json(path):
    return json.loads(Path(path).read_bytes())


def load_population(root, run_id):
    root = Path(root)
    recon = read_json(root / "recon.json")
    checks = recon.get("checks") if isinstance(recon.get("checks"), list) else []
    if (recon.get("status") != "PASS" or str(recon.get("run_id")) != str(run_id)
            or recon.get("scope") != SCOPE or not checks
            or any(not isinstance(row, dict) or row.get("status") != "PASS" for row in checks)):
        raise ValueError("Tablet source artifact is not the requested successful run")
    pages = {}
    for observation in recon.get("observations", []):
        request, fixture = observation.get("request_body"), observation.get("fixture")
        if not isinstance(request, dict) or not isinstance(fixture, str):
            continue
        raw = (root / fixture).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != observation.get("fixture_sha256"):
            raise ValueError("Tablet pf_search fixture hash mismatch")
        offset = int(request["startIndex"])
        page = json.loads(raw)
        if offset in pages and pages[offset][0] != page:
            raise ValueError("Tablet pf_search page changed at a duplicate offset")
        pages[offset] = (page, digest)
    if not pages:
        raise ValueError("Tablet source artifact contains no pf_search pages")
    offsets = sorted(pages)
    population = pf_population([pages[offset][0] for offset in offsets])
    products = []
    for offset in offsets:
        page, digest = pages[offset]
        for group in page["searchResults"]:
            for variant in group["groupedProductList"]:
                sku = variant["modelCode"]
                products.append({
                    "run_id": str(run_id), "exact_sku": sku,
                    "source_claim_listing_raw": {key: variant.get(key) for key in
                        ("modelCode", "modelName", "ecomFlag", "stockFlag", "energyStarFlg")},
                    "listing": {"source_family_id": group["group_id"],
                        "representative_sku": group["modelCode"],
                        "sku_role": "REPRESENTATIVE" if sku == group["modelCode"] else "VARIANT",
                        "plp_url": PLP_URL,
                        "pdp_url": "https://www.samsung.com" + variant["pdpURL"],
                        "source_pf_search_hash": digest},
                })
    skus = [row["exact_sku"] for row in products]
    if len(skus) != population["unique_exact_skus"] or len(set(skus)) != len(skus):
        raise ValueError("Tablet exact-SKU population cardinality or uniqueness changed")
    return products, {"source_run_id": str(run_id), "scope": SCOPE, "group_count": population["total_groups"],
        "sku_count": len(products), "pf_page_count": len(offsets),
        "pf_page_hashes": [pages[offset][1] for offset in offsets]}


def shard_for(sku, count=SHARD_COUNT):
    return int.from_bytes(hashlib.sha256(sku.encode("utf-8")).digest()[:4], "big") % count


def _selected_sku(selection, target):
    controls = selection.get("selected_controls")
    if (not selection.get("continue_visible")
            or str(selection.get("continue_sku") or "").upper() != target.upper()):
        raise ValueError("Visible Tablet Continue control does not corroborate the exact SKU")
    return {"exact_sku": target,
        "identity_basis": "exact-SKU PDP URL and visible Continue control data-modelcode; selected controls retained as raw context; no purchase made",
        "selected_controls_raw": controls if isinstance(controls, list) else []}


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
            record = {"exact_sku": sku, "status": "FAILED", "requested_url": product["listing"]["pdp_url"],
                "browser_identity": browser_identity, "observed_ecom_group_ids": [],
                "captured_at": datetime.now(timezone.utc).isoformat()}
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
                # Samsung PDPs can expose multiple controls with the same accessible
                # name. Only the primary PDP Continue button carries the current SKU.
                purchase = page.locator("#continue_btn")
                purchase.wait_for(state="visible", timeout=30000)
                selection = {"selected_controls": page.locator('[data-modelcode][aria-checked="true"]').evaluate_all(
                    '(els) => els.map(e => ({sku:e.getAttribute("data-modelcode"),label:e.getAttribute("aria-label")}))'),
                    "continue_sku": purchase.get_attribute("data-modelcode") if purchase.count() else None,
                    "continue_visible": purchase.is_visible() if purchase.count() else False}
                selection_facts = _selected_sku(selection, sku)
                final = urlsplit(page.url)
                slug = re.escape(sku.lower().replace("/", "-"))
                if (response is None or response.status != 200 or final.scheme != "https"
                        or final.hostname != "www.samsung.com" or "/us/" not in final.path
                        or not re.search(r"-sku-" + slug + r"/?$", final.path.lower())):
                    raise ValueError("Tablet PDP response or final exact-SKU URL is invalid")
                unique_groups = sorted(set(group_ids))
                if len(unique_groups) != 1:
                    raise ValueError("Current Tablet PDP did not expose one unambiguous ecom-data group_id")
                record["observed_ecom_group_ids"] = unique_groups
                specs_url = "https://www.samsung.com/us/gapi/v1/bridge/cacheable/bridge-data?" + urlencode({
                    "data_type": "Specs", "store_type": "B2C", "group_id": unique_groups[0],
                    "modelCode": sku, "version": "v2"})
                specs_response = context.request.get(specs_url, timeout=30000)
                if specs_response.status != 200:
                    raise ValueError("Same-page Tablet Specs endpoint did not return HTTP 200")
                projected = project_computer_specs(specs_response.json())
                facts = pdp_facts(projected, sku, family="tablet")
                snapshot = {"target_sku": sku, **page.evaluate(DOM_SNAPSHOT),
                    "structured_records": [], "structured_probes": [], "structured_errors": []}
                snapshot_raw = (json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
                (folder / "snapshot.json").write_bytes(snapshot_raw)
                specs_raw = (json.dumps(projected, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
                (folder / "specs.json").write_bytes(specs_raw)
                claims = claim_facts(snapshot, sku, product["source_claim_listing_raw"], facts)
                record.update(status="VERIFIED_EXACT_IDENTITY", final_url=safe_url(page.url),
                    selection_identity=selection_facts, selected_configuration_raw=selection,
                    specs_url=safe_url(specs_url), specs_sha256=hashlib.sha256(specs_raw).hexdigest(),
                    snapshot_sha256=hashlib.sha256(snapshot_raw).hexdigest(), pdp_facts_raw=facts,
                    energy_star_claim_sources_raw=claims,
                    identity_contract="SELECTED_CONFIG_CONTINUE_SKU_CURRENT_ECOM_GROUP_AND_EXACT_SPECS")
            except Exception as error:
                record["error"] = str(error).splitlines()[0][:300]
            finally:
                page.close()
                (folder / "result.json").write_text(json.dumps(record, ensure_ascii=False,
                    sort_keys=True, indent=2) + "\n", encoding="utf-8")
            results.append(record)
        context.close()
        browser.close()
    return results


def build_shard(recon_root, source_run_id, shard_index, shard_count, output):
    if shard_count != SHARD_COUNT or not 0 <= shard_index < shard_count:
        raise ValueError(f"Tablet collection requires one of {SHARD_COUNT} deterministic shards")
    products, population = load_population(recon_root, source_run_id)
    selected = [row for row in products if shard_for(row["exact_sku"], shard_count) == shard_index]
    out = Path(output); out.mkdir(parents=True, exist_ok=True)
    (out / "population.json").write_text(json.dumps(population, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "products.json").write_text(json.dumps(selected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    results = collect(selected, out)
    statuses = {row["exact_sku"]: row["status"] for row in results}
    if len(statuses) != len(selected) or set(statuses) != {row["exact_sku"] for row in selected}:
        raise ValueError("Tablet shard results do not exactly cover assigned SKUs")
    summary = {"contract": CONTRACT, "source_run_id": str(source_run_id),
        "collection_run_id": os.getenv("GITHUB_RUN_ID"), "shard_index": shard_index,
        "shard_count": shard_count, "population_count": len(selected),
        "all_population_skus": sorted(row["exact_sku"] for row in products),
        "assigned_skus": sorted(statuses),
        "coverage_counts": {state: sum(value == state for value in statuses.values())
            for state in ("VERIFIED_EXACT_IDENTITY", "FAILED")},
        "rows": results, "status": "PASS" if all(value == "VERIFIED_EXACT_IDENTITY" for value in statuses.values()) else "FAILED"}
    (out / "shard-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("status", "source_run_id", "shard_index", "shard_count", "population_count", "coverage_counts")}, sort_keys=True), flush=True)
    failures = [{"exact_sku": row["exact_sku"], "error": row.get("error", "unspecified failure")}
        for row in results if row["status"] != "VERIFIED_EXACT_IDENTITY"]
    if failures:
        print(json.dumps({"tablet_collection_failures": failures}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if summary["status"] == "PASS" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recon-root", required=True); parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--shard-index", type=int, required=True); parser.add_argument("--shard-count", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    return build_shard(args.recon_root, args.source_run_id, args.shard_index, args.shard_count, args.out)


if __name__ == "__main__":
    raise SystemExit(main())

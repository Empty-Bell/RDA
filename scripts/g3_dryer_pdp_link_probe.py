"""Bounded live PDP link probe for selected Dryers without canonical Energy Guides."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from browser_runtime import desktop_context


CONTRACT = "G3_DRYER_PDP_ENERGYGUIDE_LINK_PROBE_V1"
TARGET_SKUS = ("DV90F53AESA3", "DV45DG6000HWA2", "DVE45T3200W/A3")
LINK_TERM = re.compile(r"energy\s*guide|energy[-_]?guide|energuide|energy\s*label|download.{0,30}guide", re.I)


def read_json(path):
    return json.loads(Path(path).read_bytes())


def load_targets(collection_root, collection_run_id, target_skus=TARGET_SKUS):
    root = Path(collection_root)
    summary = read_json(root / "collection-summary.json")
    if (summary.get("status") != "PASS"
            or str(summary.get("collection_run_id")) != str(collection_run_id)):
        raise ValueError("PDP link probe requires the requested successful collection")
    results = {row.get("exact_sku"): row for row in
               (read_json(path) for path in sorted(root.glob("pdp/*/result.json")))}
    products = {row.get("exact_sku"): row for row in read_json(root / "products.json")}
    if len(results) != summary.get("coverage", {}).get("population_count"):
        raise ValueError("PDP link probe collection coverage is incomplete")
    targets = []
    for sku in target_skus:
        result, product = results.get(sku), products.get(sku)
        if (not result or not product or result.get("status") != "VERIFIED_EXACT_IDENTITY"
                or result.get("pdp_facts_raw", {}).get("energyguide_documents")
                or not product.get("listings")):
            raise ValueError(f"Probe target is absent, unverified, or has a canonical Energy Guide: {sku}")
        targets.append({"exact_sku": sku, "pdp_url": product["listings"][0]["pdp_url"]})
    return targets


def inspect_page(page, target):
    response = page.goto(target["pdp_url"], wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    final_url = page.url
    if response is None or response.status != 200:
        raise ValueError(f"PDP did not load successfully for {target['exact_sku']}")
    expected_path = urlsplit(target["pdp_url"]).path.lower().rstrip("/")
    final_path = urlsplit(final_url).path.lower().rstrip("/")
    if final_path != expected_path:
        raise ValueError(f"PDP redirected away from the exact target: {target['exact_sku']}")
    if target["exact_sku"].lower() not in page.locator("body").inner_text().lower():
        raise ValueError(f"Target SKU absent from rendered PDP: {target['exact_sku']}")
    candidates = page.locator("a[href], button, [role='link']").evaluate_all("""els => els.map(e => ({
      text:(e.innerText || e.textContent || '').trim().replace(/\\s+/g,' ').slice(0,300),
      href:e.href || e.getAttribute('href') || '',
      aria:e.getAttribute('aria-label') || '', title:e.getAttribute('title') || ''
    })).filter(x => /energy\\s*guide|energy[-_]?guide|energuide|energy\\s*label|download.{0,30}guide/i
      .test([x.text,x.href,x.aria,x.title].join(' ')))""")
    page_text = page.locator("body").inner_text()
    return {"exact_sku": target["exact_sku"], "pdp_url": final_url,
            "http_status": response.status, "exact_url_identity_verified": True,
            "exact_sku_visible": True, "energyguide_term_in_rendered_page_text": bool(LINK_TERM.search(page_text)),
            "energyguide_link_candidates": candidates,
            "result_scope": "Visible rendered PDP links only; no external support search, document retrieval, or assessment"}


def probe(collection_root, collection_run_id, output):
    from playwright.sync_api import sync_playwright
    targets = load_targets(collection_root, collection_run_id)
    rows = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context, identity = desktop_context(browser)
        try:
            for target in targets:
                page = context.new_page()
                try:
                    rows.append(inspect_page(page, target))
                finally:
                    page.close()
        finally:
            context.close()
            browser.close()
    report = {"contract": CONTRACT, "status": "PASS", "collection_run_id": str(collection_run_id),
              "probe_run_id": os.getenv("GITHUB_RUN_ID"), "git_sha": os.getenv("GITHUB_SHA"),
              "captured_at": datetime.now(timezone.utc).isoformat(),
              "browser_identity": identity, "target_count": len(rows), "rows": rows,
              "scope": "Three exact-SKU Dryer PDPs without canonical Energy Guide Support entries; visible PDP link scan only; no grading"}
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "pdp-link-probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Dryer PDP visible EnergyGuide link probe\n\n")
            stream.write("| Exact SKU | PDP | Rendered EnergyGuide text | Matching link candidates |\n|---|---|---|---:|\n")
            for row in rows:
                stream.write(f"| `{row['exact_sku']}` | [PDP]({row['pdp_url']}) | {row['energyguide_term_in_rendered_page_text']} | {len(row['energyguide_link_candidates'])} |\n")
            stream.write("\nThis checks only visible PDP links/text on three samples; it does not search Samsung Support or retrieve documents.\n")
    print(json.dumps({"status": report["status"], "target_count": len(rows),
                      "energyguide_link_candidate_count": sum(len(row["energyguide_link_candidates"]) for row in rows)}, sort_keys=True), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--collection-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    probe(args.collection_root, args.collection_run_id, args.out)


if __name__ == "__main__":
    main()

"""Inspect preserved Dryer PDP Support URL metadata; never fetch or assess documents."""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit


CONTRACT = "G3_DRYER_SUPPORT_URL_INVENTORY_V1"
ENERGYGUIDE_URL = re.compile(r"energy\s*guide|energy[-_]?guide|energuide|energylabel", re.I)


def inventory(collection_root, collection_run_id):
    root = Path(collection_root)
    summary = json.loads((root / "collection-summary.json").read_bytes())
    if (summary.get("status") != "PASS"
            or str(summary.get("collection_run_id")) != str(collection_run_id)):
        raise ValueError("Support inventory requires the requested successful Dryer collection")
    expected = summary.get("coverage", {}).get("population_count")
    results = [json.loads(path.read_bytes()) for path in sorted(root.glob("pdp/*/result.json"))]
    if not isinstance(expected, int) or len(results) != expected:
        raise ValueError("Support inventory has incomplete PDP coverage")
    seen = set()
    by_pair = {}
    url_shapes = defaultdict(lambda: {"entry_count": 0, "sku_count": 0, "skus": set(), "examples": []})
    energyguide_candidates = []
    for result in results:
        sku = result.get("exact_sku")
        if (not isinstance(sku, str) or sku in seen
                or result.get("status") != "VERIFIED_EXACT_IDENTITY"):
            raise ValueError("Support inventory includes a duplicate or unverified SKU")
        seen.add(sku)
        facts = result.get("pdp_facts_raw", {})
        documents = facts.get("support_documents_raw")
        if not isinstance(documents, list):
            raise ValueError("Complete Support document projection is missing")
        for document in documents:
            if not isinstance(document, dict):
                raise ValueError("Support document row is invalid")
            name = str(document.get("name") or "(unnamed)").strip()
            dtype = str(document.get("type") or "(unspecified)").strip()
            key = (name, dtype)
            row = by_pair.setdefault(key, {"name_raw": name, "type_raw": dtype,
                                           "entry_count": 0, "skus": set()})
            row["entry_count"] += 1
            row["skus"].add(sku)
            url = document.get("url")
            if not isinstance(url, str) or not url:
                continue
            parts = urlsplit(url)
            marker = bool(ENERGYGUIDE_URL.search(url))
            shape = (name, dtype, parts.hostname or "(no host)", parts.path or "(no path)")
            shape_row = url_shapes[shape]
            shape_row["entry_count"] += 1
            shape_row["skus"].add(sku)
            if len(shape_row["examples"]) < 2:
                shape_row["examples"].append(url)
            if marker:
                energyguide_candidates.append({"exact_sku": sku, "name_raw": name,
                                               "type_raw": dtype, "url": url,
                                               "url_marker_basis": "ENERGYGUIDE_TERM_IN_URL"})
    if len(seen) != expected:
        raise ValueError("Support inventory SKU coverage changed")
    names = [{"name_raw": name, "type_raw": dtype, "entry_count": row["entry_count"],
              "sku_count": len(row["skus"])}
             for (name, dtype), row in sorted(by_pair.items(), key=lambda pair: (pair[0][0].casefold(), pair[0][1].casefold()))]
    shapes = [{"name_raw": name, "type_raw": dtype, "host": host, "url_path": path,
               "entry_count": row["entry_count"], "sku_count": len(row["skus"]),
               "energyguide_term_in_url": bool(ENERGYGUIDE_URL.search(path)),
               "example_urls": row["examples"]}
              for (name, dtype, host, path), row in sorted(url_shapes.items(), key=lambda pair: pair[0])]
    return {"contract": CONTRACT, "status": "PASS", "collection_run_id": str(collection_run_id),
            "inventory_run_id": os.getenv("GITHUB_RUN_ID"), "git_sha": os.getenv("GITHUB_SHA"),
            "captured_at": datetime.now(timezone.utc).isoformat(), "sku_population_count": expected,
            "scope": "Inspect captured Support name/type/URL metadata only; no network fetch, label matching, or assessment",
            "support_document_name_inventory": names, "support_url_shape_inventory": shapes,
            "energyguide_term_url_candidate_count": len(energyguide_candidates),
            "energyguide_term_url_candidates": energyguide_candidates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-root", required=True)
    parser.add_argument("--collection-run-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = inventory(args.collection_root, args.collection_run_id)
    destination = Path(args.out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "support-url-inventory.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("## Dryer PDP Support URL inventory\n\n")
            stream.write(f"Verified exact SKUs: **{report['sku_population_count']}**; URL candidates with EnergyGuide-like terms: **{report['energyguide_term_url_candidate_count']}**. This inspects captured URL text only; it does not fetch documents or assess labels.\n\n")
            stream.write("| Support name | Type | SKUs | Entries |\n|---|---|---:|---:|\n")
            for row in report["support_document_name_inventory"]:
                stream.write(f"| {row['name_raw']} | {row['type_raw']} | {row['sku_count']} | {row['entry_count']} |\n")
            stream.write("\n| Name | Type | Host | URL path | SKUs | URL entries | EnergyGuide term |\n|---|---|---|---|---:|---:|---|\n")
            for row in report["support_url_shape_inventory"]:
                stream.write(f"| {row['name_raw']} | {row['type_raw']} | {row['host']} | `{row['url_path']}` | {row['sku_count']} | {row['entry_count']} | {row['energyguide_term_in_url']} |\n")
            stream.write("\n")
            for row in report["energyguide_term_url_candidates"]:
                stream.write(f"- `{row['exact_sku']}` — {row['name_raw']} ({row['type_raw']}): `{row['url']}`\n")
    print(json.dumps({"status": report["status"], "sku_population_count": report["sku_population_count"],
                      "support_name_count": len(report["support_document_name_inventory"]),
                      "url_shape_count": len(report["support_url_shape_inventory"]),
                      "energyguide_term_url_candidate_count": report["energyguide_term_url_candidate_count"]}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

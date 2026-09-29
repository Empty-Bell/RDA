"""Bounded retry for transient exact-SKU PDP collection failures.

Only failed SKUs are collected again. A retry is accepted only after the
family collector verifies the same exact SKU; all earlier raw captures remain
under retries/ for source review.
"""

from pathlib import Path
import shutil
import time
from urllib.parse import quote


def retry_failed(products, destination, results, collector, *, sleep=time.sleep):
    destination = Path(destination)
    by_sku = {product["exact_sku"]: product for product in products}
    if len(by_sku) != len(products):
        raise ValueError("Retry population contains duplicate exact SKUs")
    if len(results) != len(products) or {row.get("exact_sku") for row in results} != set(by_sku):
        raise ValueError("Initial collection does not cover the exact-SKU population")
    for attempt in (2, 3):
        failed = [row for row in results if row.get("status") == "FAILED"]
        if not failed:
            break
        sleep(2 ** (attempt - 2))
        retry_root = destination / "retries" / f"attempt-{attempt}"
        expected = {row["exact_sku"] for row in failed}
        retried = collector([by_sku[sku] for sku in sorted(expected)], retry_root)
        updates = {row.get("exact_sku"): row for row in retried}
        if len(updates) != len(retried) or set(updates) != expected:
            raise ValueError("Retry returned a different exact-SKU population")
        for index, prior in enumerate(results):
            sku = prior["exact_sku"]
            candidate = updates.get(sku)
            if candidate is None or candidate.get("status") != "VERIFIED_EXACT_IDENTITY":
                continue
            sku_path = quote(sku, safe="")
            original = destination / "pdp" / sku_path
            verified = retry_root / "pdp" / sku_path
            if not original.is_dir() or not verified.is_dir():
                raise ValueError(f"Retry raw evidence is missing for {sku}")
            archive = destination / "retries" / "previous-attempts" / sku_path / "attempt-1"
            archive.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(original), str(archive))
            shutil.copytree(verified, original)
            candidate["collection_attempt"] = attempt
            results[index] = candidate
    return results

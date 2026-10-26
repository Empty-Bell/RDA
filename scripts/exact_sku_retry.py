"""Bounded retry for transient exact-SKU PDP collection failures.

Only failed SKUs are collected again. A retry is accepted only after the
family collector verifies the same exact SKU; all earlier raw captures remain
under retries/ for source review.
"""

import json
from pathlib import Path
import shutil
import time
from urllib.parse import quote

from pdp_route import confirm_route_loss as confirm_out_of_stock_route_loss, diagnostics as route_loss_diagnostics


def retry_failed(products, destination, results, collector, *, sleep=time.sleep, confirm_route_loss=False):
    destination = Path(destination)
    by_sku = {product["exact_sku"]: product for product in products}
    if len(by_sku) != len(products):
        raise ValueError("Retry population contains duplicate exact SKUs")
    if len(results) != len(products) or {row.get("exact_sku") for row in results} != set(by_sku):
        raise ValueError("Initial collection does not cover the exact-SKU population")
    attempts = {row["exact_sku"]: [row] for row in results}
    for attempt in (2, 3):
        failed = [row for row in results
                  if row.get("status") == "FAILED" and row.get("retryable", True) is not False]
        if not failed:
            break
        sleep(2 ** (attempt - 2))
        retry_root = destination / "retries" / f"attempt-{attempt}"
        expected = {row["exact_sku"] for row in failed}
        retried = collector([by_sku[sku] for sku in sorted(expected)], retry_root)
        updates = {row.get("exact_sku"): row for row in retried}
        if len(updates) != len(retried) or set(updates) != expected:
            raise ValueError("Retry returned a different exact-SKU population")
        for sku, row in updates.items():
            attempts[sku].append(row)
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
    if confirm_route_loss:
        apply_route_loss_confirmation(by_sku, destination, results, attempts)
    return results


def apply_route_loss_confirmation(by_sku, destination, results, attempts):
    """Replace a FAILED SKU by PDP_REDIRECT_CONFIRMED when all three attempts lost the PDP route
    to the same page and its PLP stockFlag is N; the failed first attempt stays archived."""
    for index, row in enumerate(results):
        sku = row["exact_sku"]
        if row.get("status") != "FAILED" or len(attempts[sku]) < 3:
            continue
        terminal = confirm_out_of_stock_route_loss(attempts[sku], by_sku[sku])
        if terminal is None:
            if row.get("retryable", True) is not False:
                row["route_loss_diagnostics"] = route_loss_diagnostics(attempts[sku], by_sku[sku])
            continue
        sku_path = quote(sku, safe="")
        original = destination / "pdp" / sku_path
        archive = destination / "retries" / "previous-attempts" / sku_path / "attempt-1"
        if original.is_dir() and not archive.exists():
            archive.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(original, archive)
        (original / "result.json").write_text(
            json.dumps(terminal, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        results[index] = terminal

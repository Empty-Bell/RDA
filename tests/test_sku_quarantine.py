"""Bounded quarantine of unverifiable exact SKUs (DECISIONS 2026-10-27)."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import sku_quarantine as q


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def single(root, statuses):
    rows = [{"exact_sku": sku, "status": status, **({"error": "boom"} if status == "FAILED" else {})}
            for sku, status in sorted(statuses.items())]
    counts = {state: sum(row["status"] == state for row in rows)
              for state in ("VERIFIED_EXACT_IDENTITY", "FAILED", "NOT_ATTEMPTED")}
    failed = counts["FAILED"] or counts["NOT_ATTEMPTED"]
    write(root / "collection-summary.json", {
        "status": "FAILED" if failed else "PASS", "collection_run_id": "1",
        "coverage": {"population_count": len(rows), "attempted_count": len(rows), "counts": counts, "rows": rows}})
    write(root / "products.json", [{"exact_sku": sku} for sku in sorted(statuses)])
    for sku, status in statuses.items():
        if status != "NOT_ATTEMPTED":
            write(root / "pdp" / sku / "result.json", {"exact_sku": sku, "status": status,
                                                      "requested_url": f"https://www.samsung.com/us/x-sku-{sku}/"})


class AllowanceTest(unittest.TestCase):
    def test_two_and_five_percent_rounded_up(self):
        self.assertEqual([q.allowance(n) for n in (1, 10, 20, 21, 40, 41, 166)], [1, 1, 1, 2, 2, 2, 2])


class SingleCollectionTest(unittest.TestCase):
    def test_failed_sku_moves_out_and_collection_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            statuses = {f"SKU{i:02d}": "VERIFIED_EXACT_IDENTITY" for i in range(21)}
            statuses["SKU05"] = "FAILED"
            single(root / "c", statuses)
            entries = q.quarantine_single(root / "c", root / "quarantine")
            summary = json.loads((root / "c/collection-summary.json").read_text())
            products = json.loads((root / "c/products.json").read_text())
            self.assertEqual([e["exact_sku"] for e in entries], ["SKU05"])
            self.assertEqual(entries[0]["status"], "UNVERIFIED")
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(summary["coverage"]["population_count"], 20)
            self.assertEqual(summary["coverage"]["counts"]["FAILED"], 0)
            self.assertNotIn("SKU05", {p["exact_sku"] for p in products})
            self.assertFalse((root / "c/pdp/SKU05").exists())
            self.assertTrue((root / "quarantine/pdp/SKU05/result.json").is_file())
            self.assertEqual(json.loads((root / "quarantine/original/collection-summary.json").read_text())["status"], "FAILED")

    def test_over_allowance_keeps_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            statuses = {f"SKU{i:02d}": "VERIFIED_EXACT_IDENTITY" for i in range(10)}
            statuses["SKU01"] = statuses["SKU02"] = "FAILED"
            single(root / "c", statuses)
            with self.assertRaises(q.QuarantineRefused):
                q.quarantine_single(root / "c", root / "quarantine")
            self.assertTrue((root / "c/pdp/SKU01").is_dir())

    def test_unattempted_sku_is_never_quarantined(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            statuses = {f"SKU{i:02d}": "VERIFIED_EXACT_IDENTITY" for i in range(30)}
            statuses["SKU03"] = "NOT_ATTEMPTED"
            single(root / "c", statuses)
            with self.assertRaises(q.QuarantineRefused):
                q.quarantine_single(root / "c", root / "quarantine")

    def test_clean_collection_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            single(root / "c", {"A": "VERIFIED_EXACT_IDENTITY", "B": "VERIFIED_EXACT_IDENTITY"})
            before = (root / "c/collection-summary.json").read_text()
            with mock.patch.dict(os.environ, {q.DRILL_ENV: ""}):
                self.assertEqual(q.quarantine_single(root / "c", root / "quarantine"), [])
            self.assertEqual((root / "c/collection-summary.json").read_text(), before)

    def test_drill_quarantines_one_verified_sku_off_main(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            single(root / "c", {f"S{i}": "VERIFIED_EXACT_IDENTITY" for i in range(5)})
            with mock.patch.dict(os.environ, {q.DRILL_ENV: "1", "GITHUB_REF": "refs/heads/feature"}):
                entries = q.quarantine_single(root / "c", root / "quarantine")
            self.assertEqual([(e["exact_sku"], e["drill"], e["error"]) for e in entries], [("S0", True, q.DRILL_ERROR)])

    def test_drill_refused_on_main(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            single(root / "c", {"A": "VERIFIED_EXACT_IDENTITY"})
            with mock.patch.dict(os.environ, {q.DRILL_ENV: "1", "GITHUB_REF": "refs/heads/main"}):
                with self.assertRaises(q.QuarantineRefused):
                    q.quarantine_single(root / "c", root / "quarantine")


class ShardTest(unittest.TestCase):
    STATES = ("VERIFIED_EXACT_IDENTITY", "PDP_REDIRECT_CONFIRMED", "FAILED")

    def build(self, root, assignment):
        population = sorted(sku for skus in assignment.values() for sku in skus)
        for index, skus in assignment.items():
            shard = root / f"shard-{index}"
            rows = [{"exact_sku": sku, "status": status} for sku, status in sorted(skus.items())]
            write(shard / "shard-summary.json", {
                "status": "FAILED" if any(r["status"] == "FAILED" for r in rows) else "PASS",
                "shard_index": index, "shard_count": len(assignment), "population_count": len(rows),
                "all_population_skus": population, "assigned_skus": sorted(skus), "rows": rows,
                "coverage_counts": {}})
            write(shard / "products.json", [{"exact_sku": sku} for sku in sorted(skus)])
            for sku in skus:
                write(shard / "pdp" / sku / "result.json", {"exact_sku": sku, "status": skus[sku]})

    def test_shard_failure_is_removed_from_every_shard_population(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.build(root / "c", {0: {"A": "VERIFIED_EXACT_IDENTITY", "B": "FAILED"},
                                    1: {"C": "PDP_REDIRECT_CONFIRMED", "D": "VERIFIED_EXACT_IDENTITY"}})
            entries = q.quarantine_shards(root / "c", root / "quarantine", self.STATES)
            self.assertEqual([e["exact_sku"] for e in entries], ["B"])
            for index in (0, 1):
                item = json.loads((root / f"c/shard-{index}/shard-summary.json").read_text())
                self.assertEqual(item["status"], "PASS")
                self.assertEqual(item["all_population_skus"], ["A", "C", "D"])
            self.assertTrue((root / "quarantine/shard-0/pdp/B/result.json").is_file())
            self.assertFalse((root / "c/shard-0/pdp/B").exists())

    def test_shard_failures_above_allowance_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.build(root / "c", {0: {"A": "FAILED", "B": "FAILED"}, 1: {"C": "VERIFIED_EXACT_IDENTITY"}})
            with self.assertRaises(q.QuarantineRefused):
                q.quarantine_shards(root / "c", root / "quarantine", self.STATES)


if __name__ == "__main__":
    unittest.main()

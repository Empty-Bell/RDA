"""Bounded retries retain every raw attempt and never substitute a variant."""

from pathlib import Path
import tempfile
import unittest

from exact_sku_retry import retry_failed


class ExactSkuRetryTest(unittest.TestCase):
    def test_transient_failure_recovers_same_sku_and_keeps_raw_attempt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "pdp" / "WF45T6000AW%2FA5"
            original.mkdir(parents=True)
            (original / "result.json").write_text("wrong redirect", encoding="utf-8")
            calls = []

            def collector(products, output):
                calls.append([product["exact_sku"] for product in products])
                folder = output / "pdp" / "WF45T6000AW%2FA5"
                folder.mkdir(parents=True)
                (folder / "result.json").write_text("verified exact SKU", encoding="utf-8")
                return [{"exact_sku": "WF45T6000AW/A5", "status": "VERIFIED_EXACT_IDENTITY"}]

            result = retry_failed([{"exact_sku": "WF45T6000AW/A5"}], root,
                                  [{"exact_sku": "WF45T6000AW/A5", "status": "FAILED"}],
                                  collector, sleep=lambda _: None)
            self.assertEqual(calls, [["WF45T6000AW/A5"]])
            self.assertEqual(result[0]["collection_attempt"], 2)
            self.assertEqual((original / "result.json").read_text(), "verified exact SKU")
            archived = root / "retries" / "previous-attempts" / "WF45T6000AW%2FA5" / "attempt-1" / "result.json"
            self.assertEqual(archived.read_text(), "wrong redirect")

    def test_persistent_failure_stays_failed_after_three_attempts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            calls = []

            def collector(products, output):
                calls.append(output.name)
                return [{"exact_sku": "WF45T6000AW/A5", "status": "FAILED"}]

            result = retry_failed([{"exact_sku": "WF45T6000AW/A5"}], root,
                                  [{"exact_sku": "WF45T6000AW/A5", "status": "FAILED"}],
                                  collector, sleep=lambda _: None)
            self.assertEqual(calls, ["attempt-2", "attempt-3"])
            self.assertEqual(result[0]["status"], "FAILED")

    def test_retry_cannot_substitute_another_sku(self):
        with tempfile.TemporaryDirectory() as temp:
            def collector(products, output):
                return [{"exact_sku": "WF45T6000AV/A5", "status": "VERIFIED_EXACT_IDENTITY"}]

            with self.assertRaisesRegex(ValueError, "different exact-SKU"):
                retry_failed([{"exact_sku": "WF45T6000AW/A5"}], Path(temp),
                             [{"exact_sku": "WF45T6000AW/A5", "status": "FAILED"}],
                             collector, sleep=lambda _: None)

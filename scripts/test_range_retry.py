"""Bounded exact-SKU retry contracts for transient Range PDP redirects."""

from pathlib import Path
import tempfile
import unittest

from g3_range_collect import retry_failed


class RangeRetryTest(unittest.TestCase):
    def test_successful_retry_keeps_both_raw_attempts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "pdp" / "NSG90H60SWAA"
            original.mkdir(parents=True)
            (original / "result.json").write_text('wrong variant', encoding="utf-8")
            calls = []

            def collector(products, destination):
                calls.append(products[0]["exact_sku"])
                folder = destination / "pdp" / "NSG90H60SWAA"
                folder.mkdir(parents=True)
                (folder / "result.json").write_text('verified exact SKU', encoding="utf-8")
                return [{"exact_sku": "NSG90H60SWAA", "status": "VERIFIED_EXACT_IDENTITY"}]

            result = retry_failed([{"exact_sku": "NSG90H60SWAA"}], root,
                                  [{"exact_sku": "NSG90H60SWAA", "status": "FAILED"}], collector)
            self.assertEqual(calls, ["NSG90H60SWAA"])
            self.assertEqual(result[0]["collection_attempt"], 2)
            self.assertEqual((original / "result.json").read_text(), 'verified exact SKU')
            self.assertEqual((root / "retries/previous-attempts/NSG90H60SWAA/attempt-1/result.json").read_text(),
                             'wrong variant')

    def test_persistent_redirect_stays_failed_after_three_attempts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attempts = []

            def collector(products, destination):
                attempts.append(destination.name)
                return [{"exact_sku": "NSG90H60SWAA", "status": "FAILED"}]

            result = retry_failed([{"exact_sku": "NSG90H60SWAA"}], root,
                                  [{"exact_sku": "NSG90H60SWAA", "status": "FAILED"}], collector)
            self.assertEqual(attempts, ["attempt-2", "attempt-3"])
            self.assertEqual(result[0]["status"], "FAILED")

    def test_retry_cannot_substitute_another_variant(self):
        with tempfile.TemporaryDirectory() as temp:
            def collector(products, destination):
                return [{"exact_sku": "NSG90H60SRAA", "status": "VERIFIED_EXACT_IDENTITY"}]

            with self.assertRaisesRegex(ValueError, "different exact-SKU"):
                retry_failed([{"exact_sku": "NSG90H60SWAA"}], Path(temp),
                             [{"exact_sku": "NSG90H60SWAA", "status": "FAILED"}], collector)


if __name__ == "__main__":
    unittest.main()

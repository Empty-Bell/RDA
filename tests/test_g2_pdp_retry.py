"""Refrigerator retry preserves source identity and earlier raw captures."""

from pathlib import Path
import tempfile
import unittest

from g2_pdp import retry_failed_samples


class G2PdpRetryTest(unittest.TestCase):
    def test_failed_identity_recovers_without_replacing_earlier_raw(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "first.json"
            first.write_text("wrong redirect", encoding="utf-8")
            calls = []

            def collector(products, output):
                calls.append(products[0]["exact_sku"])
                output.mkdir(parents=True)
                raw = output / "result.json"
                raw.write_text("verified", encoding="utf-8")
                return [{"exact_sku": "RF25C5A01SRAA", "status": "VERIFIED_EXACT_IDENTITY",
                         "observations": [{"path": str(raw)}]}]

            result = retry_failed_samples(
                [{"exact_sku": "RF25C5A01SRAA"}],
                [{"exact_sku": "RF25C5A01SRAA", "status": "FAILED",
                  "observations": [{"path": str(first)}]}],
                root / "retries", collector, sleep=lambda _: None,
            )
            self.assertEqual(calls, ["RF25C5A01SRAA"])
            self.assertEqual(result[0]["collection_attempt"], 2)
            self.assertEqual(first.read_text(), "wrong redirect")
            self.assertEqual(Path(result[0]["observations"][0]["path"]).read_text(), "verified")

    def test_wrong_variant_cannot_replace_exact_sku(self):
        with tempfile.TemporaryDirectory() as temp:
            def collector(products, output):
                return [{"exact_sku": "RF25C5A01SRBA", "status": "VERIFIED_EXACT_IDENTITY"}]

            with self.assertRaisesRegex(ValueError, "different exact-SKU"):
                retry_failed_samples(
                    [{"exact_sku": "RF25C5A01SRAA"}],
                    [{"exact_sku": "RF25C5A01SRAA", "status": "FAILED"}],
                    Path(temp), collector, sleep=lambda _: None,
                )

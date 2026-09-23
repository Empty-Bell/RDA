"""Offline contracts for the Tablet exact-SKU collector."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from g3_tablet_collect import SHARD_COUNT, _selected_sku, load_population, shard_for

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "tablet" / "pf-page-0.json"
RUN_ID = "35159081725"


def make_recon(root, *, status="PASS", run_id=RUN_ID, scope="tablet source contracts only", digest=None):
    raw = FIXTURE.read_bytes()
    (root / "fixtures").mkdir()
    (root / "fixtures" / "pf-0.json").write_bytes(raw)
    recon = {"status": status, "run_id": run_id, "scope": scope,
        "checks": [{"name": "plp_request_contract", "status": "PASS"}],
        "observations": [{"request_body": {"startIndex": "0"}, "fixture": "fixtures/pf-0.json",
            "fixture_sha256": digest or hashlib.sha256(raw).hexdigest()}]}
    (root / "recon.json").write_text(json.dumps(recon), encoding="utf-8")


class TabletCollectTests(unittest.TestCase):
    def test_complete_source_fixture_yields_unique_exact_skus(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); make_recon(root)
            products, metadata = load_population(root, RUN_ID)
        skus = [row["exact_sku"] for row in products]
        self.assertEqual(len(skus), len(set(skus)))
        self.assertEqual(len(products), metadata["sku_count"])
        self.assertEqual("SM-X930NZAAXAR", products[0]["exact_sku"])
        self.assertEqual("tablet source contracts only", metadata["scope"])

    def test_wrong_source_run_or_failed_source_is_rejected(self):
        for kwargs in ({"run_id": "other"}, {"status": "FAILED"}, {"scope": "computer source contracts only"}):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); make_recon(root, **kwargs)
                with self.assertRaisesRegex(ValueError, "requested successful run"):
                    load_population(root, RUN_ID)

    def test_changed_source_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); make_recon(root, digest="0" * 64)
            with self.assertRaisesRegex(ValueError, "fixture hash mismatch"):
                load_population(root, RUN_ID)

    def test_selected_configuration_and_continue_must_both_match_exact_sku(self):
        good = {"selected_controls": [{"sku": "sm-x930nzaaxar"}],
            "continue_sku": "SM-X930NZAAXAR", "continue_visible": True}
        self.assertEqual("SM-X930NZAAXAR", _selected_sku(good, "SM-X930NZAAXAR")["exact_sku"])
        for bad in (
            {**good, "selected_controls": [{"sku": "SM-X930NZAAXAA"}]},
            {**good, "continue_sku": "SM-X930NZAAXAA"},
            {**good, "continue_visible": False},
            {**good, "selected_controls": []},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                _selected_sku(bad, "SM-X930NZAAXAR")

    def test_shards_are_stable_and_cover_skus_once(self):
        self.assertEqual(SHARD_COUNT, 4)
        skus = [f"SM-X{index:06d}AA" for index in range(100)]
        first = {sku: shard_for(sku) for sku in skus}
        self.assertEqual(first, {sku: shard_for(sku) for sku in skus})
        self.assertEqual(set(range(SHARD_COUNT)), set(first.values()))
        self.assertEqual(len(skus), sum(sum(shard_for(sku) == i for sku in skus) for i in range(SHARD_COUNT)))


if __name__ == "__main__":
    unittest.main()

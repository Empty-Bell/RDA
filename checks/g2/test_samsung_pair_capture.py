import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_samsung_pair_capture import (  # noqa: E402
    project_declared_pair,
    replay_capture,
    source_record,
)

FIXTURE = ROOT / "tests" / "fixtures" / "g2-samsung-pair" / "declared-pair.html"


class SamsungPairCaptureTests(unittest.TestCase):
    def test_sanitized_official_pair_fixture_is_observational(self):
        projection = project_declared_pair(FIXTURE.read_bytes())
        self.assertEqual(projection["raw_field"], "RF23DB9600QL / RF23DB9600QLAA")
        self.assertEqual(projection["left_identifier"], "RF23DB9600QL")
        self.assertEqual(projection["right_identifier"], "RF23DB9600QLAA")
        self.assertEqual(projection["identity_state"], "NOT_EVALUATED")

    def test_missing_duplicate_and_literal_sku_suffix_are_withheld(self):
        for body in (
            b"",
            b"RF23DB9600QL / RF23DB9600QLAA RF23DB9600QL / RF23DB9600QLAA",
            b"RF18A5101SR/AA",
        ):
            with self.assertRaises(ValueError):
                project_declared_pair(body)

    def test_failed_or_empty_source_is_rejected(self):
        with self.assertRaises(ValueError):
            source_record(403, "text/html", b"blocked")
        with self.assertRaises(ValueError):
            source_record(200, "text/html", b"")

    def test_replay_binds_raw_bytes_and_projection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            body = FIXTURE.read_bytes()
            record = {
                "name": "samsung-rf23db9600qlaa-pdp",
                "body_sha256": hashlib.sha256(body).hexdigest(),
            }
            (root / (record["name"] + ".bin")).write_bytes(body)
            (root / "manifest.json").write_text(
                json.dumps({"source": record, "projection": project_declared_pair(body)}),
                encoding="utf-8",
            )
            self.assertEqual(replay_capture(root)["projection"]["left_identifier"], "RF23DB9600QL")
            (root / (record["name"] + ".bin")).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash"):
                replay_capture(root)

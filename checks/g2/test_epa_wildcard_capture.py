import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_epa_wildcard_capture import replay_capture, source_record


class EpaWildcardCaptureTests(unittest.TestCase):
    def test_source_record_rejects_failed_or_empty_response(self):
        with self.assertRaises(ValueError):
            source_record("x", "https://example.com", 403, "text/html", b"no")
        with self.assertRaises(ValueError):
            source_record("x", "https://example.com", 200, "text/html", b"")

    def test_replay_requires_exact_preserved_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = b"official source"
            (root / "x.bin").write_bytes(raw)
            (root / "manifest.json").write_text(
                json.dumps(
                    {"sources": [{"name": "x", "body_sha256": hashlib.sha256(raw).hexdigest()}]}
                ),
                encoding="utf-8",
            )
            self.assertEqual(replay_capture(root)["sources"][0]["name"], "x")
            (root / "x.bin").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash"):
                replay_capture(root)

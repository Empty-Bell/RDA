import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_epa_disqualified_capture import (  # noqa: E402
    discover_xlsx_url,
    project_source,
    replay_capture,
)


PAGE = b'<a href="/files/List%20of%20Products%20Disqualified_DQPL.xlsx">Excel</a>'
XLSX = b"PK\x03\x04sanitized-xlsx-container"


class EpaDisqualifiedCaptureTests(unittest.TestCase):
    def test_discovers_exact_official_xlsx_link_without_parsing_rows(self):
        self.assertEqual(
            discover_xlsx_url(PAGE, "https://www.energystar.gov/integrity"),
            "https://www.energystar.gov/files/List%20of%20Products%20Disqualified_DQPL.xlsx",
        )
        self.assertEqual(
            project_source("disqualified-list", XLSX)["content_state"], "XLSX_BYTES_ONLY_NOT_PARSED"
        )

    def test_missing_ambiguous_or_non_xlsx_container_is_rejected(self):
        for page in (b"<html></html>", PAGE + PAGE.replace(b"DQPL", b"disqualified-2")):
            with self.assertRaises(ValueError):
                discover_xlsx_url(page)
        with self.assertRaises(ValueError):
            project_source("disqualified-list", b"<html>error</html>")

    def test_replay_requires_original_bytes_and_discovered_url(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "integrity-page.bin").write_bytes(PAGE)
            (root / "disqualified-list.bin").write_bytes(XLSX)
            url = discover_xlsx_url(PAGE)
            manifest = {
                "sources": [
                    {"name": "integrity-page", "body_sha256": hashlib.sha256(PAGE).hexdigest()},
                    {
                        "name": "disqualified-list",
                        "requested_url": url,
                        "body_sha256": hashlib.sha256(XLSX).hexdigest(),
                    },
                ],
                "projections": {
                    "integrity-page": project_source("integrity-page", PAGE),
                    "disqualified-list": project_source("disqualified-list", XLSX),
                },
            }
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(replay_capture(root), manifest)
            (root / "disqualified-list.bin").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash"):
                replay_capture(root)

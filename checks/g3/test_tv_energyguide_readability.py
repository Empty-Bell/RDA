"""TV labels protected by NASCA are explicit HIGH evidence, not silent gaps."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.g3_dishwasher_energyguide_observe import verified_pdf_population


class TvEnergyGuideReadability(unittest.TestCase):
    def write_fixture(self, root, failed_prefix):
        pdf = b"%PDF-1.7 readable test fixture"
        digest = hashlib.sha256(pdf).hexdigest()
        (root / "pdf").mkdir()
        (root / "pdf" / "readable.pdf").write_bytes(pdf)
        readable_url = "https://images.samsung.com/readable.pdf"
        blocked_url = "https://images.samsung.com/blocked.pdf"
        report = {
            "status": "PARTIAL",
            "retrieval_run_id": "42",
            "failed_url_count": 1,
            "url_count": 2,
            "pdf_hash_count": 1,
            "url_observations": [
                {"url": readable_url, "status": "RETRIEVED_VALID_PDF", "sha256": digest,
                 "path": "pdf/readable.pdf"},
                {"url": blocked_url, "status": "FAILED", "body_prefix_hex": failed_prefix},
            ],
            "records": [
                {"exact_sku": "TV-ONE", "source_document_index": 0, "url": readable_url,
                 "retrieval": {"sha256": digest}},
                {"exact_sku": "TV-TWO", "source_document_index": 0, "url": blocked_url,
                 "retrieval": {"error": "unreadable"}},
            ],
        }
        (root / "energyguide-summary.json").write_text(json.dumps(report), encoding="utf-8")

    def test_nasca_server_drm_is_high_and_readable_pdfs_remain_available(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_fixture(root, b"<## NASCA DRM FILE - VER1.00".hex())
            pdfs, source = verified_pdf_population(root, "42", allow_nasca_drm=True)
        self.assertEqual(len(pdfs), 1)
        self.assertEqual(source["unreadable_documents"][0]["state"], "NOT_ACCESSIBLE")
        self.assertEqual(source["unreadable_documents"][0]["severity"], "HIGH")
        self.assertEqual(source["unreadable_documents"][0]["issue_code"],
                         "ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE")

    def test_other_failed_download_is_not_downgraded_to_partial(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_fixture(root, b"<html>access denied".hex())
            with self.assertRaisesRegex(ValueError, "failed PDF URLs"):
                verified_pdf_population(root, "42", allow_nasca_drm=True)


if __name__ == "__main__":
    unittest.main()

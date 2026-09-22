"""TV labels protected by NASCA are explicit HIGH evidence, not silent gaps."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.g3_dishwasher_energyguide_observe import verified_pdf_population
from scripts.g3_tv_source_comparison import compare_single_candidates, epa_watts, extract_kwh, extract_watts


class TvEnergyGuideReadability(unittest.TestCase):
    def test_annual_kwh_and_watts_are_compared_only_with_like_units(self):
        self.assertEqual(extract_kwh("208 W"), None)
        self.assertEqual(extract_watts("208 W"), "208")
        self.assertEqual(extract_kwh("408 kWh/year"), "408")
        self.assertEqual(extract_watts("408 kWh/year"), None)
        self.assertEqual(epa_watts("117.69"), "117.69")
        self.assertEqual(compare_single_candidates(["408"], ["408"], "NO_LABEL", "NO_EPA")["status"],
                         "EXACT_VALUE_MATCH")
        self.assertEqual(compare_single_candidates(["408"], ["390"], "NO_LABEL", "NO_EPA")["status"],
                         "VALUES_DIFFER")

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
            with self.assertRaisesRegex(ValueError, "other than explicitly allowed NASCA DRM"):
                verified_pdf_population(root, "42", allow_nasca_drm=True)


if __name__ == "__main__":
    unittest.main()

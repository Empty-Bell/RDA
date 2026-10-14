import json
import tempfile
import unittest
from pathlib import Path

from scripts.g3_dishwasher_energyguide_observe import verified_pdf_population


class DishwasherUnreadableEnergyGuideObservationTests(unittest.TestCase):
    def test_explicit_unreadable_declared_document_is_carried_as_high_finding(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            url = "https://images.samsung.com/is/content/samsung/example.pdf"
            summary = {
                "status": "PARTIAL",
                "retrieval_run_id": "run-1",
                "failed_url_count": 0,
                "unreadable_url_count": 1,
                "url_count": 1,
                "pdf_hash_count": 0,
                "url_observations": [{
                    "url": url,
                    "status": "DECLARED_DOCUMENT_UNREADABLE",
                    "severity": "HIGH",
                    "issue_code": "ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE",
                    "reason": "DECLARED_ENERGYGUIDE_RESPONSE_IS_NOT_A_PDF",
                    "http_status": 200,
                    "content_type": "text/html",
                    "byte_count": 21,
                    "body_sha256": "a" * 64,
                    "body_prefix_hex": "3c68746d6c3e",
                }],
                "records": [{
                    "exact_sku": "DW70H83YETRAA",
                    "source_document_index": 0,
                    "url": url,
                    "name_raw": "Energy Guide",
                    "type_raw": "PDF",
                    "retrieval": {
                        "status": "DECLARED_DOCUMENT_UNREADABLE",
                        "issue_code": "ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE",
                    },
                }],
            }
            (root / "energyguide-summary.json").write_text(json.dumps(summary), encoding="utf-8")
            pdfs, source = verified_pdf_population(
                root,
                "run-1",
                allow_declared_unreadable=True,
            )
        self.assertEqual(pdfs, {})
        self.assertEqual(source["sku_document_count"], 0)
        self.assertEqual(len(source["unreadable_documents"]), 1)
        finding = source["unreadable_documents"][0]
        self.assertEqual(finding["exact_sku"], "DW70H83YETRAA")
        self.assertEqual(finding["severity"], "HIGH")
        self.assertEqual(finding["issue_code"], "ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE")


if __name__ == "__main__":
    unittest.main()

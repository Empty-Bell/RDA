"""Dryer EnergyGuide raw-candidate index contracts; no field selection."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.g3_dryer_energyguide_review_queue import review


class DryerEnergyGuideReviewContract(unittest.TestCase):
    def make_artifact(self, root):
        digest = "a" * 64
        pdf_dir = root / "pdf" / digest
        pdf_dir.mkdir(parents=True)
        source = {
            "sku_documents": [{"exact_sku": "DV90F53AESA3", "pdf_sha256": digest,
                               "source_document_index": 0, "url": "https://www.samsung.com/guide.pdf"}],
            "sku_document_count": 1,
            "sku_population_count": 1,
            "sku_document_coverage": [{"exact_sku": "DV90F53AESA3", "support_document_count": 1,
                                        "state": "DOCUMENTS_DECLARED"}],
        }
        observation = {
            "pdf_sha256": digest,
            "page_count": 1,
            "source_urls": ["https://www.samsung.com/guide.pdf"],
            "label_heading_observations": {"us_energyguide_heading_candidates": [],
                                           "canada_energuide_heading_candidates": []},
            "pages": [{"page": 1, "spans_raw": [{"engine": "PyMuPDF"}],
                       "fields_raw": {
                           "model_candidates_raw": [{"value_raw": "DV90F8**0***", "context_raw": "Models DV90F8**0***"}],
                           "energy_candidates_raw": [{"value_raw": "608", "role": "ANNUAL_CAPTION_CONTEXT"}],
                           "capacity_candidates_raw": [{"value_raw": "Drying Capacity (cu.ft) 7.6"}],
                       }}],
        }
        (pdf_dir / "observation.json").write_text(json.dumps(observation), encoding="utf-8")
        summary = {"status": "PASS", "observation_run_id": "123", "retrieval_run_id": "456",
                   "observed_pdf_count": 1, "source": source,
                   "observations": [{"status": "OBSERVED", "pdf_sha256": digest,
                                     "observation_path": f"pdf/{digest}/observation.json"}]}
        (root / "observation-summary.json").write_text(json.dumps(summary), encoding="utf-8")

    def test_indexes_dryer_candidates_without_selecting_or_assessing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "in"
            root.mkdir()
            out = Path(directory) / "out"
            self.make_artifact(root)
            report = review(root, "123", out)
            row = report["table"][0]
            self.assertEqual(row["models_raw"], ["DV90F8**0***"])
            self.assertEqual(row["annual_kwh_raw"], ["608"])
            self.assertEqual(row["capacity_raw"], ["Drying Capacity (cu.ft) 7.6"])
            self.assertEqual(report["entries"][0]["selection"], "NOT_EVALUATED")
            self.assertEqual(report["entries"][0]["assessment"], "NOT_EVALUATED")

    def test_wrong_observation_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_artifact(root)
            with self.assertRaisesRegex(ValueError, "requested successful run"):
                review(root, "wrong-run", root / "out")


if __name__ == "__main__":
    unittest.main()

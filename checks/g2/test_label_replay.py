import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from g2_label_replay import replay  # noqa: E402


class LabelReplayTests(unittest.TestCase):
    def test_replays_one_hash_for_multiple_exact_skus(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "source.zip"
            annual_path = root / "annual.json"
            capacity_path = root / "capacity.json"
            digest = hashlib.sha256(b"shared-pdf").hexdigest()
            proposal = {
                "number_detection": 22,
                "unit_detection": 23,
                "value_raw": "500",
            }
            candidates = {
                "pdf_sha256": digest,
                "energy_candidates_raw": [{
                    "value_raw": "500",
                    "unit_raw": "kWh",
                    "role": "ANNUAL_CAPTION_CONTEXT",
                    "matched_text": "500 kWh",
                }],
                "capacity_candidates_raw": [{
                    "value_raw": "Capacity: 20.0 Cubic Feet"
                }],
            }
            layout = {
                "pdf_sha256": digest,
                "annual_layout_candidates": [{
                    "page": 0,
                    "caption_detection": 24,
                    "nearest_proposal_raw": proposal,
                    "proposals_raw": [proposal],
                }],
            }
            checkpoint = {
                "status": "PASS",
                "run_id": "run-1",
                "label_selection_summary": {"records": [
                    {"exact_sku": sku, "source_document_index": 0, "pdf_sha256": digest}
                    for sku in ("SKU-A", "SKU-B")
                ]},
            }
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("g2/run/checkpoint.json", json.dumps(checkpoint))
                base = "g2/run/energyguide-samples/SKU-A/0"
                archive.writestr(
                    f"{base}/energyguide-field-candidates.json", json.dumps(candidates)
                )
                archive.writestr(
                    f"{base}/energyguide-layout-candidates.json", json.dumps(layout)
                )
            annual_path.write_text(json.dumps({
                "contract": "MANUAL_VISUAL_REVIEW_BINDING_ONLY",
                "annotations": [{
                    "exact_skus": ["SKU-A", "SKU-B"],
                    "pdf_sha256": digest,
                    "document_count": 1,
                    "all_pages_reviewed": True,
                    "us_panel_verified": True,
                    "page": 0,
                    "caption_detection": 24,
                    "number_detection": 22,
                    "unit_detection": 23,
                    "expected_observation": {"state": "VALUE", "amount": 500.0},
                }],
            }), encoding="utf-8")
            capacity_path.write_text(json.dumps({
                "contract": "CAPACITY_MODEL_REVIEW_PROJECTION_ONLY",
                "records": [{
                    "exact_skus": ["SKU-A", "SKU-B"],
                    "pdf_sha256": digest,
                    "document_count": 1,
                    "all_pages_reviewed": True,
                    "us_panel_verified": True,
                    "page": 0,
                    "capacity_detection": 8,
                    "capacity_bbox": [[0, 0], [1, 0], [1, 1], [0, 1]],
                    "capacity_text_raw": "Capacity: 20.0 Cubic Feet",
                }],
            }), encoding="utf-8")

            report = replay(archive_path, annual_path, capacity_path)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(
                report["label_selection_summary"]["counts"],
                {"VALUE": 2, "NOT_OBSERVED": 0},
            )
            self.assertEqual(
                report["capacity_selection_summary"]["counts"],
                {"VALUE": 2, "NOT_OBSERVED": 0},
            )
            self.assertEqual(report["overall_product_compliance"], "NOT_EVALUATED")


if __name__ == "__main__":
    unittest.main()

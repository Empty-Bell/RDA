import json
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_label_quality_report import build_quality_profile, render_markdown  # noqa: E402


def observation(value=None, state="VALUE"):
    return {"state": state, "value": value if state == "VALUE" else None, "error": None}


class LabelQualityReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.archive = Path(self.temp.name) / "artifact.zip"
        self.pdf_bytes = b"%PDF-1.4\nsynthetic-label\n%%EOF\n"
        self.pdf_sha256 = hashlib.sha256(self.pdf_bytes).hexdigest()
        products = [{"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}]
        facts = []
        for sku in ("SKU-A", "SKU-B"):
            facts.append({
                "kind": "ENERGYGUIDE", "exact_sku": sku,
                "observations": {
                    "document_sha256": observation(self.pdf_sha256),
                    "document_status": observation("SOURCE_PDF_PARSED"),
                    "extraction_engine": observation("RapidOCR"),
                    "fallback_reason": observation("EMPTY_EMBEDDED_TEXT"),
                    "label_model_raw": observation("SKU-**"),
                },
            })
        checkpoint = {
            "status": "PASS", "run_id": "run-1",
            "label_selection_summary": {"records": [
                {"exact_sku": "SKU-A", "annual_energy_observation": observation(500),
                 "selection_reason": "REVIEWED"},
                {"exact_sku": "SKU-B", "annual_energy_observation": observation(state="NOT_OBSERVED"),
                 "selection_reason": "NO_REVIEW"},
            ]},
            "capacity_selection_summary": {"records": [
                {"exact_sku": "SKU-A", "capacity_observation": observation(20),
                 "selection_reason": "REVIEWED"},
                {"exact_sku": "SKU-B", "capacity_observation": observation(state="NOT_OBSERVED"),
                 "selection_reason": "NO_REVIEW"},
            ]},
        }
        bundle = {"manifest": {"run_id": "run-1", "git_sha": "b" * 40},
                  "products": products, "facts": facts}
        with zipfile.ZipFile(self.archive, "w") as zipped:
            zipped.writestr("g2/run/checkpoint.json", json.dumps(checkpoint))
            zipped.writestr("g2/run/bundle.json", json.dumps(bundle))
            for sku in ("SKU-A", "SKU-B"):
                base = f"g2/run/energyguide-samples/{sku}/0"
                zipped.writestr(f"{base}/energyguide-original.pdf", self.pdf_bytes)
                zipped.writestr(f"{base}/energyguide-field-candidates.json", json.dumps({
                    "pdf_sha256": self.pdf_sha256,
                    "model_candidates_raw": [{"value_raw": "SKU-**"}],
                    "energy_candidates_raw": [{"value_raw": "500", "unit_raw": "kWh",
                                                 "role": "ANNUAL_CAPTION_CONTEXT"}],
                    "capacity_candidates_raw": [{"value_raw": "Capacity: 20 Cubic Feet"}],
                }))

    def tearDown(self):
        self.temp.cleanup()

    def test_profiles_exact_sku_and_pdf_hash_grain(self):
        profile = build_quality_profile(self.archive, github_run_id="123")
        counts = profile["counts"]
        self.assertEqual(counts["population_exact_skus"], 2)
        self.assertEqual(counts["unique_pdf_hashes"], 1)
        self.assertEqual(counts["shared_pdf_hash_groups"], 1)
        self.assertEqual(counts["annual_energy_values"], 1)
        self.assertEqual(counts["raw_model_not_observed"], 0)
        self.assertEqual(counts["annual_energy_not_observed_pdf_hashes"], 0)
        self.assertEqual(profile["pdf_groups"][0]["candidates"]["model_values_raw"], ["SKU-**"])
        self.assertEqual(profile["overall_product_compliance"], "NOT_EVALUATED")
        report = render_markdown(profile)
        self.assertIn("| 2 | 2 | 1 | 2 | 0 |", report)
        self.assertIn("## PDF-hash review queue", report)

    def test_rejects_incomplete_fact_or_review_coverage(self):
        with zipfile.ZipFile(self.archive, "r") as source:
            checkpoint = json.loads(source.read("g2/run/checkpoint.json"))
            bundle = json.loads(source.read("g2/run/bundle.json"))
        bundle["facts"].pop()
        broken = Path(self.temp.name) / "broken.zip"
        with zipfile.ZipFile(broken, "w") as zipped:
            zipped.writestr("g2/run/checkpoint.json", json.dumps(checkpoint))
            zipped.writestr("g2/run/bundle.json", json.dumps(bundle))
        with self.assertRaisesRegex(ValueError, "fact coverage"):
            build_quality_profile(broken)


if __name__ == "__main__":
    unittest.main()

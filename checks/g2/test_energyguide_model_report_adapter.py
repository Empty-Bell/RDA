from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from g2_energyguide_model_report_adapter import attach_model_pattern_assessment, add_model_pattern_section  # noqa: E402


class ModelPatternReportAdapterTests(unittest.TestCase):
    def test_attaches_only_reviewed_sku_slice(self):
        bundle = {"manifest": {"run_id": "run-1"}, "products": [{"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}]}
        assessment = {"contract": "G2_ENERGYGUIDE_REVIEW_BOUND_MODEL_PATTERN_ASSESSMENT_V1", "status": "PASS", "assessment_enabled": True,
                      "source": {"execution_run_id": "run-1"}, "counts": {"display": {"PASS": 1, "NOT_EVALUATED": 0}},
                      "records": [{"exact_sku": "SKU-A", "display_outcome": "PASS", "assessment": "MODEL_PATTERN_INCLUDED", "matching_patterns": ["SKU-*"], "label_pdf_sha256": "a" * 64}]}
        with tempfile.NamedTemporaryFile(delete=False) as artifact:
            artifact.write(b"assessment")
            artifact_path = artifact.name
        try:
            section = attach_model_pattern_assessment(bundle, assessment, artifact_path)
            report = {"run_id": "run-1", "assessment_enabled": False, "rows": [{"exact_sku": "SKU-A"}, {"exact_sku": "SKU-B"}]}
            add_model_pattern_section(report, section)
            self.assertEqual(report["energyguide_model_pattern"]["coverage"], {"reviewed_exact_skus": 1})
        finally:
            Path(artifact_path).unlink(missing_ok=True)

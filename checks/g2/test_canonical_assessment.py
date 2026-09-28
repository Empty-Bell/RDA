import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from g2_canonical_assessment import promote, RULE_VERSION


class CanonicalAssessmentTests(unittest.TestCase):
    def inputs(self, root):
        raw = b'[{"model_number":"SKU-A"}]'
        digest = hashlib.sha256(raw).hexdigest()
        (root / "page-0000.bin").write_bytes(raw)
        (root / "manifest.json").write_text(json.dumps({
            "run_id": "run-1", "status": "PASS", "captured_at": "2026-01-01T00:00:00Z",
            "sources": [{"name": "page-0000", "file": "page-0000.bin", "url": "https://data.energystar.gov/example",
                         "body_sha256": digest, "status": 200}],
        }), encoding="utf-8")
        bundle = {"manifest": {"run_id": "run-1", "assessment_enabled": False},
                  "products": [{"exact_sku": "SKU-A"}],
                  "facts": [{"exact_sku": "SKU-A", "kind": kind, "evidence_ids": [key]}
                            for kind, key in (("PDP", "pdp"), ("ENERGYGUIDE", "label"))],
                  "evidence": [{"sku": "SKU-A", "evidence_id": "pf", "evidence_type": "projected-public-pf-response"}],
                  "assessments": [{"assessment_status": "NOT_EVALUATED"}]}
        star = {"source_run_id": "run-1", "records": [{"exact_sku": "SKU-A", "outcome": "HIGH",
                "severity": "HIGH", "issue_code": "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE",
                "publication_points": {"pdp_logo": "PRESENT"}, "epa_current_index_registration": {"state": "ABSENT"}}]}
        numeric = {"source": {"execution_run_id": "run-1"}, "records": [{"exact_sku": "SKU-A",
                   "display_outcome": "PASS", "finding_count": 0, "findings": []}]}
        model = {"source": {"execution_run_id": "run-1"}, "records": [{"exact_sku": "SKU-A",
                 "display_outcome": "PASS", "matching_patterns": ["SKU*"],
                 "normalized_identifier": "SKU-A", "label_pdf_sha256": digest}]}

        def evidence(data, url, sku, kind, captured_at):
            key = f"epa-{len(bundle['evidence'])}"
            bundle["evidence"].append({"sku": sku, "evidence_id": key, "evidence_type": kind})
            return key, hashlib.sha256(data).hexdigest()
        return bundle, star, numeric, model, evidence

    def test_promotes_all_controls_and_keeps_epa_raw_page_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, star, numeric, model, evidence = self.inputs(root)
            with patch("g2_canonical_assessment.validate_bundle"):
                promote(bundle, star, numeric, model, root, evidence)
        self.assertEqual(bundle["manifest"]["rule_version"], RULE_VERSION)
        self.assertEqual(bundle["manifest"]["overall_execution_status"], "SUCCESS")
        self.assertEqual(len(bundle["assessments"]), 3)
        self.assertEqual(sum(item["assessment_status"] == "FINDING" for item in bundle["assessments"]), 1)
        self.assertTrue(any(key.startswith("epa-") for key in bundle["assessments"][0]["evidence_ids"]))

    def test_rejects_unresolved_model_control(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, star, numeric, model, evidence = self.inputs(root)
            model["records"][0]["matching_patterns"] = []
            with self.assertRaisesRegex(ValueError, "model control is unresolved"):
                promote(bundle, star, numeric, model, root, evidence)

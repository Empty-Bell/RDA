import copy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from g2_label_plan import declared_energyguide_documents
from source_contract import pdp_facts


class LabelPlanTests(unittest.TestCase):
    def setUp(self):
        bridge = json.loads((ROOT / "tests/fixtures/refrigerator/bridge-specs-support.json").read_text(encoding="utf-8"))
        self.sku = "RF29DB9900QDAA"
        self.facts = pdp_facts(bridge, self.sku)

    def test_actual_support_fixture_keeps_declared_document_without_selection(self):
        plan = declared_energyguide_documents([{"exact_sku": self.sku, "status": "VERIFIED_EXACT_IDENTITY", "pdp_facts_raw": self.facts}])
        self.assertEqual(plan["rows"][0]["document_status"], "DECLARED_BY_EXACT_SUPPORT")
        self.assertEqual(plan["canonical_document_selection"], "NOT_EVALUATED")
        self.assertTrue(plan["rows"][0]["documents"][0]["url"].startswith("https://"))

    def test_missing_support_document_is_not_a_successful_label(self):
        facts = copy.deepcopy(self.facts)
        facts["energyguide_documents"] = []
        plan = declared_energyguide_documents([{"exact_sku": self.sku, "status": "VERIFIED_EXACT_IDENTITY", "pdp_facts_raw": facts}])
        self.assertEqual(plan["rows"][0]["document_status"], "NOT_OBSERVED")
        self.assertEqual(plan["selected_document_count"], 0)

    def test_duplicate_sku_is_rejected(self):
        result = {"exact_sku": self.sku, "status": "VERIFIED_EXACT_IDENTITY", "pdp_facts_raw": self.facts}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            declared_energyguide_documents([result, result])

    def test_non_https_document_is_rejected(self):
        facts = copy.deepcopy(self.facts)
        facts["energyguide_documents"][0]["url"] = "http://example.test/label.pdf"
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            declared_energyguide_documents([{"exact_sku": self.sku, "status": "VERIFIED_EXACT_IDENTITY", "pdp_facts_raw": facts}])

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from g3_tv_source_comparison import explicit_additional_models


class TVAdditionalModelTests(unittest.TestCase):
    def row(self, **changes):
        return {"brand_name": "Samsung", "markets": "United States", "date_qualified": "2025-02-10",
                "pd_id": "3994365", "model_number": "QN77S85FAE",
                "additional_model_information": "QN77S84FAE,QN77S84FAE,Same as basic model except designation",
                **changes}

    def test_explicit_additional_model_is_included(self):
        matches = explicit_additional_models(self.row(), "QN77S84FAEXZA")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["model_number_raw"], "QN77S84FAE")
        self.assertEqual(matches[0]["certified_row_model_number_raw"], "QN77S85FAE")

    def test_similar_or_unverified_model_is_rejected(self):
        for sku in ("QN77S84FAFXZA", "QN77S84FAEAA", "QN77S84FAEZZZ"):
            with self.subTest(sku=sku):
                self.assertEqual(explicit_additional_models(self.row(), sku), [])
        self.assertEqual(explicit_additional_models(self.row(markets="Canada"), "QN77S84FAEXZA"), [])
        self.assertEqual(explicit_additional_models(self.row(date_qualified=""), "QN77S84FAEXZA"), [])
        self.assertEqual(explicit_additional_models(
            self.row(additional_model_information="QN77S84FAE,QN77S84FDE,nearby"), "QN77S84FAEXZA"), [])


if __name__ == "__main__":
    unittest.main()

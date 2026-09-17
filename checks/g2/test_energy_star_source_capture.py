from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_energy_star_source_capture import extract_next_products, project_group_declarations  # noqa: E402


def next_html(products):
    import json
    return ('<script id="__NEXT_DATA__" type="application/json">' + json.dumps({
        "props": {"pageProps": {"productData": {"products": products}}}
    }) + "</script>").encode()


def bridge(skus):
    return {
        "Specs": [{"modelCode": sku, "fullSpecs": [{"groupName": "Key Features", "specList": [
            {"name": "ENERGY STAR Certified", "value": "Yes"}
        ]}]} for sku in skus],
        "Support": [{"modelCode": sku, "supports": []} for sku in skus],
    }


class EnergyStarDirectSourceTests(unittest.TestCase):
    def test_next_projection_keeps_exact_sku_and_raw_flag(self):
        result = extract_next_products(next_html([{"modelCode": "SKU-A", "energyStarFlag": "Y"}]))
        self.assertEqual(result, [{"exact_sku": "SKU-A", "pdp_energy_star_flag_raw": "Y"}])

    def test_variants_use_their_own_pf_and_next_values(self):
        group = {
            "group_id": "MULTI_GROUP_ID_1", "modelCode": "REP", "pdpURL": "/us/x-sku-rep",
            "groupedProductList": [
                {"modelCode": "REP", "pdpURL": "/us/x-sku-rep", "energyStarFlg": "Y"},
                {"modelCode": "VAR", "pdpURL": "/us/x-sku-var", "energyStarFlg": "N"},
            ],
        }
        rows = project_group_declarations(group, next_html([
            {"modelCode": "REP", "energyStarFlag": "Y"},
            {"modelCode": "VAR", "energyStarFlag": "N"},
        ]), bridge(["REP", "VAR"]))
        self.assertEqual(rows[0]["plp_energy_star_flag_raw"], "Y")
        self.assertEqual(rows[1]["plp_energy_star_flag_raw"], "N")
        self.assertEqual(rows[0]["pdp_energy_star_flag_raw"], "Y")
        self.assertEqual(rows[1]["pdp_energy_star_flag_raw"], "N")
        self.assertEqual(rows[1]["sku_role"], "VARIANT")

    def test_next_sku_set_must_equal_pf_group(self):
        group = {"group_id": "MULTI_GROUP_ID_1", "modelCode": "REP", "pdpURL": "/us/x-sku-rep",
                 "groupedProductList": [{"modelCode": "REP", "pdpURL": "/us/x-sku-rep", "energyStarFlg": "Y"}]}
        with self.assertRaisesRegex(ValueError, "exact SKU set"):
            project_group_declarations(group, next_html([{"modelCode": "OTHER", "energyStarFlag": "Y"}]), bridge(["REP"]))


if __name__ == "__main__":
    unittest.main()

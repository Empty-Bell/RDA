import unittest

from plp_population import select_listed_products


class PlpOptionPopulationTests(unittest.TestCase):
    def test_card_and_group_option_are_both_retained(self):
        products = [
            {"exact_sku": "CARD", "listings": [{"sku_role": "REPRESENTATIVE"}]},
            {"exact_sku": "COLOR", "listings": [{"sku_role": "VARIANT"}]},
        ]
        selected = select_listed_products(products, {"CARD": {"url": "/card"}}, 2)
        self.assertEqual({row["exact_sku"] for row in selected}, {"CARD", "COLOR"})
        self.assertEqual(selected[1]["listings"][0]["sku_role"], "VARIANT")

    def test_missing_group_option_is_never_silently_published(self):
        with self.assertRaisesRegex(ValueError, "incomplete exact-SKU coverage"):
            select_listed_products([{"exact_sku": "CARD"}], {"CARD": {}}, 2)


if __name__ == "__main__":
    unittest.main()

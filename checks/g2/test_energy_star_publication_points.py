from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from g2_energy_star_publication_points import (  # noqa: E402
    ABSENT, PRESENT, UNKNOWN, collect_publication_points, plp_logo_point,
    pdp_logo_point, spec_certification_point,
)


class PublicationPointTests(unittest.TestCase):
    def test_plp_image_is_required_for_logo(self):
        card = {"sku": "SKU", "logo_inspection": "SUPPORTED_CARD_COMPLETE", "energy_candidates": [{"tag": "SPAN", "text": "Energy Star", "src": None}]}
        self.assertEqual(plp_logo_point([card], "SKU")["state"], ABSENT)
        card["energy_candidates"] = [{"tag": "IMG", "src": "https://example/energy-star.png"}]
        self.assertEqual(plp_logo_point([card], "SKU")["state"], PRESENT)

    def test_spec_requires_affirmative_visible_row_and_never_infers_absence(self):
        snapshot = {"visible_spec_energy_star_rows": [{"text": "Energy Star certified", "cells": []}]}
        self.assertEqual(spec_certification_point(snapshot, "SKU", "VERIFIED_EXACT_IDENTITY")["state"], PRESENT)
        snapshot["visible_spec_energy_star_rows"] = []
        self.assertEqual(spec_certification_point(snapshot, "SKU", "VERIFIED_EXACT_IDENTITY")["state"], UNKNOWN)
        snapshot["spec_surface_inspection"] = "SUPPORTED_VISIBLE_SPEC_TABLE_COMPLETE"
        self.assertEqual(spec_certification_point(snapshot, "SKU", "VERIFIED_EXACT_IDENTITY")["state"], ABSENT)

    def test_pdp_logo_requires_exact_primary_image_and_can_confirm_absence(self):
        snapshot = {
            "product_jsonld": [{"sku": "SKU", "mpn": None}],
            "primary_logo_inspection": "SUPPORTED_PRIMARY_SURFACE_COMPLETE",
            "energy_candidates": [],
        }
        self.assertEqual(pdp_logo_point(snapshot, "SKU", "VERIFIED_EXACT_IDENTITY")["state"], ABSENT)
        snapshot["energy_candidates"] = [{
            "tag": "IMG", "src": "/us/b2c_pf/badge/energy-star-logo-pdp-m@2x.png",
            "product_surface": "CURRENT_GALLERY", "surface_count": 1,
        }]
        self.assertEqual(pdp_logo_point(snapshot, "SKU", "VERIFIED_EXACT_IDENTITY")["state"], PRESENT)

    def test_missing_visual_snapshot_is_unknown(self):
        result = collect_publication_points([], [{"exact_sku": "SKU", "status": "VERIFIED_EXACT_IDENTITY"}], {})
        self.assertEqual(result["records"][0]["pdp_logo"]["state"], UNKNOWN)
        self.assertEqual(result["records"][0]["pdp_spec_certification"]["state"], UNKNOWN)


if __name__ == "__main__":
    unittest.main()

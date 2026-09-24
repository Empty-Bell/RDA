"""Offline source-contract tests for Tablet EPA candidates (no assessment)."""
import json
from pathlib import Path
import tempfile
import unittest

from epa_only_rules import model_pattern_candidate
from g3_tablet_epa_candidates import additional_patterns, build_candidates, load_collection
from source_contract import epa_contract

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "epa-query" / "rxdj-2c88.json"


class TabletEpaCandidateTests(unittest.TestCase):
    def test_current_epa_fixture_satisfies_computer_schema_contract(self):
        fixture = json.loads(FIXTURE.read_bytes())
        contract = epa_contract(fixture["metadata_before"], fixture["rows_before"], dataset="rxdj-2c88")
        self.assertEqual("rxdj-2c88", contract["dataset_id"])
        self.assertEqual("NOT_EVALUATED", contract["certification_matching"])

    def test_candidate_match_is_literal_or_positional_and_never_a_prefix_guess(self):
        exact = model_pattern_candidate("SM-X930NZAAXAR", "SM-X930NZAAXAR")
        wildcard = model_pattern_candidate("SM-X93*", "SM-X930NZAAXAR")
        self.assertEqual("LITERAL_EXACT", exact["candidate_basis"])
        self.assertEqual("SM-X930", wildcard["matched_prefix_raw"])
        self.assertIsNone(model_pattern_candidate("SM-X930", "SM-X930NZAAXAR"))

    def test_additional_model_tokens_drop_explanatory_text(self):
        self.assertEqual(["SM-X930", "SM-X930*"], additional_patterns(
            "SM-X930, SM-X930*; Same as base model except designation"))

    def test_candidate_output_keeps_registration_and_publication_not_evaluated(self):
        sku = "SM-X930NZAAXAR"
        source_row = {"source_row_id": "sanitized-row", "pd_id": "sanitized-id",
            "brand_name": "Samsung", "model_number": "SM-X93*", "type": "Slate/Tablet",
            "operating_system_name": "Android", "markets": "United States"}
        products = {sku: {"source_claim_listing_raw": {"modelCode": sku}}}
        records = {sku: {"selected_configuration_raw": {"continue_sku": sku}}}
        claims = {sku: {"exact_sku": sku}}
        facts = {sku: {"exact_sku": sku}}
        with tempfile.TemporaryDirectory() as temp:
            report = build_candidates([sku], products, records, claims, facts, [source_row],
                "source-run", {"capture_run_id": "epa-run"}, temp)
            saved = json.loads((Path(temp) / "tablet-epa-source-candidates.json").read_bytes())
        self.assertEqual("SOURCE_CANDIDATES_READY", report["status"])
        self.assertEqual("NOT_EVALUATED", saved["records"][0]["registration_and_publication_assessment"])
        self.assertEqual(1, len(saved["records"][0]["epa_computer_model_pattern_candidates"]))
        self.assertIn("NO PREFIX", saved["matching_contract"])

    def test_collection_source_from_another_or_incomplete_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "shard-0").mkdir()
            (root / "shard-0" / "shard-summary.json").write_text(json.dumps({
                "contract": "G3_TABLET_EXACT_SKU_PDP_V1", "status": "FAILED",
                "collection_run_id": "wrong-run"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "incomplete or from the wrong run"):
                load_collection(root, "expected-run")


if __name__ == "__main__":
    unittest.main()

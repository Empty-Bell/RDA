"""Fixture contract for raw model review provenance and withheld identity diagnostics."""

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from g2_model_identity import diagnose_literal_model_equality, validate_model_review


class ModelIdentityContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(
            (ROOT / "tests/fixtures/g2-model-identity/review.json").read_text(encoding="utf-8")
        )
        self.review = self.fixture["review"]
        self.digest = self.review["pdf_sha256"]

    def test_review_requires_complete_bound_provenance(self):
        self.assertEqual(validate_model_review(self.review), self.review)
        for key in ("reviewer_id", "render_sha256", "box", "reviewed_at"):
            broken = copy.deepcopy(self.review)
            broken.pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_model_review(broken)

    def test_changed_bytes_or_raw_token_cannot_reuse_review(self):
        changed_bytes = diagnose_literal_model_equality(
            raw_token=self.review["raw_token"],
            product_model=self.review["raw_token"],
            pdf_sha256="0" * 64,
            review=self.review,
        )
        self.assertEqual(changed_bytes["review_status"], "REVIEW_PROVENANCE_MISMATCH")
        changed_token = diagnose_literal_model_equality(
            raw_token="RF18A5101X",
            product_model="RF18A5101X",
            pdf_sha256=self.digest,
            review=self.review,
        )
        self.assertEqual(changed_token["review_status"], "REVIEW_PROVENANCE_MISMATCH")

    def test_only_nonwildcard_literal_equality_is_a_diagnostic(self):
        literal = diagnose_literal_model_equality(
            raw_token="RF18A5101", product_model="RF18A5101", pdf_sha256=self.digest, review=None
        )
        self.assertEqual(literal["identity_diagnostic"], "LITERAL_EQUALITY_DIAGNOSTIC_ONLY")
        self.assertEqual(literal["identity_state"], "NOT_EVALUATED")
        self.assertEqual(literal["correction_state"], "NOT_APPLIED")

    def test_wildcard_suffix_and_confusion_cases_withhold_identity(self):
        cases = (
            ("RF23D*9600**", "RF23DB9600QLAA", "WITHHELD_WILDCARD_SEMANTICS"),
            ("RF18A5101", "RF18A5101/AA", "WITHHELD_SUFFIX_OR_FORMAT_VARIATION"),
            ("RF2BA5101", "RF28A5101", "WITHHELD_NONLITERAL_OR_CONFUSION_DIFFERENCE"),
        )
        for raw, product, expected in cases:
            with self.subTest(raw=raw, product=product):
                outcome = diagnose_literal_model_equality(
                    raw_token=raw, product_model=product, pdf_sha256=self.digest, review=None
                )
                self.assertEqual(outcome["identity_diagnostic"], expected)
                self.assertEqual(outcome["identity_state"], "NOT_EVALUATED")

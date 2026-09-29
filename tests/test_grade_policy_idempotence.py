"""Repeated dashboard refreshes do not grow the grade policy text."""

import unittest

from refresh_pages_dishwasher import MODEL_IDENTITY_POLICY, normalized_grade_policy


class GradePolicyIdempotenceTest(unittest.TestCase):
    def test_repeated_refresh_keeps_one_clause(self):
        base = "PASS/HIGH/MEDIUM/LOW are mutually exclusive model grades."
        policy = base + (" " + MODEL_IDENTITY_POLICY) * 15
        result = normalized_grade_policy(policy)
        self.assertEqual(result, f"{base} {MODEL_IDENTITY_POLICY}")
        self.assertEqual(normalized_grade_policy(result), result)

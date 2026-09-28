"""Lifecycle contracts for validated audit history."""

import unittest
from pathlib import Path
import tempfile

from audit_history import advance, empty, rule_fingerprint


def snapshot(number, models):
    rows = []
    for model, issue in models:
        rows.append({"family": "TV", "model": model, "grade": "HIGH" if issue else "PASS",
                     "findings": [{"control": "ENERGYGUIDE", "issue_code": issue,
                                   "severity": "HIGH"}] if issue else []})
    return {"run_number": number, "built_at": f"2026-09-{number:02d}T00:00:00+00:00",
            "records": rows}


class HistoryLifecycleTest(unittest.TestCase):
    def test_rule_fingerprint_is_checkout_line_ending_independent(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "src" / "rule.py"
            source.parent.mkdir()
            source.write_bytes(b"a = 1\nb = 2\n")
            unix = rule_fingerprint(temp)
            source.write_bytes(b"a = 1\r\nb = 2\r\n")
            self.assertEqual(rule_fingerprint(temp), unix)

    def test_independent_confirmation_and_reopening(self):
        history, first = advance(empty(), snapshot(1, [("M1", "LABEL_MISSING")]), "run-1", "rules-a")
        self.assertEqual(len(first["new"]), 1)
        history, second = advance(history, snapshot(2, [("M1", "LABEL_MISSING")]), "run-2", "rules-a")
        self.assertFalse(second["resolved"])
        self.assertEqual(history["findings"][0]["first_seen_at"], "2026-09-01T00:00:00+00:00")
        self.assertEqual(history["findings"][0]["latest_seen_at"], "2026-09-02T00:00:00+00:00")
        history, candidate = advance(history, snapshot(3, [("M1", None)]), "run-3", "rules-a")
        self.assertEqual(len(candidate["pending_confirmation"]), 1)
        self.assertEqual(history["findings"][0]["state"], "OPEN")
        self.assertEqual(history["findings"][0]["confirmation_candidate"]["observed_at"],
                         "2026-09-03T00:00:00+00:00")
        history, _ = advance(history, snapshot(4, [("M1", None)]), "failed-4", "rules-a", failed=True)
        self.assertEqual(history["findings"][0]["state"], "OPEN")
        history, confirmed = advance(history, snapshot(4, [("M1", None)]), "run-4", "rules-a")
        self.assertEqual(len(confirmed["resolved"]), 1)
        self.assertEqual(history["findings"][0]["resolved_run"], "run-4")
        self.assertEqual(history["findings"][0]["resolved_at"], "2026-09-04T00:00:00+00:00")
        history, reopened = advance(history, snapshot(5, [("M1", "LABEL_MISSING")]), "run-5", "rules-a")
        self.assertEqual(len(reopened["recurred"]), 1)
        self.assertEqual(history["findings"][0]["state"], "REOPENED")

    def test_out_of_scope_and_rule_change_do_not_resolve(self):
        history, _ = advance(empty(), snapshot(1, [("M1", "LABEL_MISSING")]), "run-1", "rules-a")
        history, _ = advance(history, snapshot(2, []), "run-2", "rules-a")
        self.assertEqual(history["findings"][0]["last_observation"], "OUT_OF_SCOPE")
        history, changed = advance(history, snapshot(3, [("M1", None)]), "run-3", "rules-b")
        self.assertFalse(changed["resolved"])
        self.assertEqual(history["findings"][0]["last_observation"], "RULESET_CHANGED")
        history, candidate = advance(history, snapshot(4, [("M1", None)]), "run-4", "rules-b")
        self.assertEqual(len(candidate["pending_confirmation"]), 1)
        history, confirmed = advance(history, snapshot(5, [("M1", None)]), "run-5", "rules-b")
        self.assertEqual(len(confirmed["resolved"]), 1)

    def test_replay_is_idempotent_but_conflicting_replay_fails(self):
        first = snapshot(1, [("M1", "LABEL_MISSING")])
        history, _ = advance(empty(), first, "run-1", "rules-a")
        again, changes = advance(history, first, "run-1", "rules-a")
        self.assertEqual(again, history)
        self.assertTrue(all(not rows for rows in changes.values()))
        with self.assertRaisesRegex(ValueError, "different findings"):
            advance(history, snapshot(1, [("M1", None)]), "run-1", "rules-a")

    def test_new_population_is_not_an_old_finding_resolution(self):
        history, _ = advance(empty(), snapshot(1, [("M1", "LABEL_MISSING")]), "run-1", "rules-a")
        history, change = advance(history, snapshot(2, [("M2", None)]), "run-2", "rules-a")
        self.assertFalse(change["resolved"])
        self.assertEqual(history["validated_runs"][-1]["scope_added"], [["TV", "M2"]])
        self.assertEqual(history["validated_runs"][-1]["scope_removed"], [["TV", "M1"]])


if __name__ == "__main__":
    unittest.main()

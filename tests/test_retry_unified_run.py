"""Recovery retries transient source jobs, never failed audit or build gates."""

import unittest

from retry_unified_run import decision


RUN = {"name": "Unified 11-family full audit", "head_branch": "main",
       "status": "completed", "conclusion": "failure", "run_attempt": 1}


class RetryUnifiedRunTest(unittest.TestCase):
    def test_family_bootstrap_failure_is_eligible(self):
        jobs = [{"name": "Acquire and assess washer", "conclusion": "failure",
                 "steps": [{"name": "Bootstrap locked browser, PDF and OCR runtime",
                            "conclusion": "failure"}]},
                {"name": "Verify one source run and 11 graded populations", "conclusion": "failure"}]
        self.assertEqual(decision(RUN, jobs, 3), "retry_family_runtime_or_artifact_failure")

    def test_family_collection_or_parser_failure_requires_review(self):
        jobs = [{"name": "Acquire and assess dishwasher", "conclusion": "failure",
                 "steps": [{"name": "Acquire current sources and apply approved family controls",
                            "conclusion": "failure"}]},
                {"name": "Verify one source run and 11 graded populations", "conclusion": "failure"}]
        self.assertEqual(decision(RUN, jobs, 3), "family_failure_requires_review")

    def test_build_bug_is_not_retried(self):
        jobs = [{"name": "Build validated Pages snapshot from this run", "conclusion": "failure",
                 "steps": [{"name": "Build and gate exactly one source snapshot", "conclusion": "failure"}]}]
        self.assertEqual(decision(RUN, jobs, 3), "report_or_browser_code_failure")

    def test_recovery_stops_after_three_attempts(self):
        jobs = [{"name": "Acquire and assess washer", "conclusion": "failure",
                 "steps": [{"name": "Bootstrap locked browser, PDF and OCR runtime",
                            "conclusion": "failure"}]}]
        self.assertEqual(decision({**RUN, "run_attempt": 3}, jobs, 3), "attempt_limit")

    def test_other_failed_gate_blocks_source_retry(self):
        jobs = [{"name": "Acquire and assess washer", "conclusion": "failure"},
                {"name": "Build validated Pages snapshot from this run", "conclusion": "failure"}]
        self.assertEqual(decision(RUN, jobs, 3), "non_source_failure")

    def test_family_checkout_failure_can_retry(self):
        jobs = [{"name": "Acquire and assess range", "conclusion": "failure",
                 "steps": [{"name": "Run actions/checkout@deadbeef", "conclusion": "failure"}]}]
        self.assertEqual(decision(RUN, jobs, 3), "retry_family_runtime_or_artifact_failure")

    def test_family_failure_without_step_evidence_is_not_retried(self):
        jobs = [{"name": "Acquire and assess range", "conclusion": "failure"}]
        self.assertEqual(decision(RUN, jobs, 3), "family_failure_requires_review")

    def test_install_failure_can_retry(self):
        jobs = [{"name": "Build validated Pages snapshot from this run", "conclusion": "failure",
                 "steps": [{"name": "Install browser for desktop and mobile smoke", "conclusion": "failure"}]}]
        self.assertEqual(decision(RUN, jobs, 3), "retry_build_dependency_or_artifact")

    def test_source_gate_failure_is_not_retried_as_artifact_failure(self):
        jobs = [{"name": "Verify one source run and 11 graded populations", "conclusion": "failure",
                 "steps": [{"name": "Reconcile all family artifacts and source identities", "conclusion": "failure"}]}]
        self.assertEqual(decision(RUN, jobs, 3), "source_gate_failure")

    def test_publication_service_failure_can_retry(self):
        jobs = [{"name": "Deploy only the validated artifact", "conclusion": "failure"}]
        self.assertEqual(decision(RUN, jobs, 3), "retry_publication_service")

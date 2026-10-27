"""Deferred final retry pacing for live public-source reads."""

import os
import unittest
from unittest import mock

from source_retry_policy import ENV, pause_before_final_retry


class DeferredRetryTest(unittest.TestCase):
    def test_unset_means_no_wait(self):
        waits = []
        with mock.patch.dict(os.environ, {ENV: ""}):
            self.assertEqual(pause_before_final_retry("x", waits.append), 0)
        self.assertEqual(waits, [])

    def test_hosted_cooldown_waits_once(self):
        waits = []
        with mock.patch.dict(os.environ, {ENV: "600"}):
            self.assertEqual(pause_before_final_retry("x", waits.append), 600)
        self.assertEqual(waits, [600])

    def test_out_of_range_is_rejected(self):
        with mock.patch.dict(os.environ, {ENV: "7200"}):
            with self.assertRaises(ValueError):
                pause_before_final_retry("x", lambda _: None)


if __name__ == "__main__":
    unittest.main()

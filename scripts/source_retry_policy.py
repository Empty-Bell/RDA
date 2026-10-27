"""Pacing for retries of live public-source reads.

Immediate retries tend to observe the same transient source state. Before the
final retry of a failed exact SKU or source step, wait the hosted cooldown in
RDA_DEFERRED_RETRY_SECONDS (unset or 0 means no wait, e.g. in unit tests).
A retry only repeats acquisition; it never relaxes an identity or source check.
"""

import json
import os
import time


ENV = "RDA_DEFERRED_RETRY_SECONDS"


def deferred_seconds():
    value = os.getenv(ENV, "").strip() or "0"
    seconds = int(value)
    if not 0 <= seconds <= 3600:
        raise ValueError(f"{ENV} must be between 0 and 3600 seconds")
    return seconds


def pause_before_final_retry(label, sleep=time.sleep):
    seconds = deferred_seconds()
    if seconds:
        print(json.dumps({"deferred_retry": label, "seconds": seconds}), flush=True)
        sleep(seconds)
    return seconds

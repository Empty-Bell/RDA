"""Replay validated snapshots after proving a platform-only ruleset fingerprint change.

The caller supplies every saved model snapshot in validated-run order. This
tool checks their stored grade/finding digests before changing history.
"""

import argparse
import json
from pathlib import Path

from audit_history import advance, empty, model_transitions, read, rule_fingerprint, snapshot_facts, write


def rebuild(prior_path, snapshots, out_history, out_current, repo_root):
    prior = read(prior_path)
    runs = prior["validated_runs"]
    if len(runs) != len(snapshots) or len(runs) < 2:
        raise ValueError("Supply every validated snapshot in order")
    canonical = rule_fingerprint(repo_root)
    if runs[-1]["ruleset"] != canonical:
        raise ValueError("Latest hosted ruleset differs from normalized current rules")
    if len({run["ruleset"] for run in runs}) != 2:
        raise ValueError("Expected exactly one historical platform fingerprint difference")
    history = empty()
    current = None
    for run, path in zip(runs, snapshots):
        snapshot = read(path)
        _, _, digest = snapshot_facts(snapshot)
        if (run["snapshot_digest"] != digest or run["run_number"] != snapshot["run_number"]):
            raise ValueError(f"Stored source snapshot differs: {run['run_id']}")
        history, current = advance(history, snapshot, run["run_id"], canonical)
    latest = read(snapshots[-1])
    previous = read(snapshots[-2])
    lifecycle = model_transitions(current, previous, latest)
    for kind in ("new", "resolved", "recurred", "pending_confirmation"):
        latest["run_comparison"][kind] = lifecycle[kind]
    write(out_history, history)
    Path(out_current).write_text(json.dumps(latest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "run_id": runs[-1]["run_id"],
                      "ruleset": canonical,
                      "transitions": {key: len(value) for key, value in lifecycle.items()}},
                     ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", required=True)
    parser.add_argument("--snapshots", nargs="+", required=True)
    parser.add_argument("--out-history", required=True)
    parser.add_argument("--out-current", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    rebuild(args.history, args.snapshots, args.out_history, args.out_current, args.repo_root)

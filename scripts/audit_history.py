"""Track finding lifecycles across validated, independent source runs.

The current model grade remains a snapshot fact. A vanished finding remains
OPEN until a second, distinct successful source run independently observes
the same model without it under the same ruleset.
"""

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path


CONTRACT = "RDA_FINDING_HISTORY_V1"
GRADES = {"PASS", "HIGH", "MEDIUM", "LOW"}
ACTIVE = {"NEW", "OPEN", "REOPENED"}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rule_fingerprint(repo_root):
    """Fingerprint the implemented source/assessment rules, not dashboard code."""
    root = Path(repo_root)
    paths = sorted(set(root.glob("scripts/g2_*assessment*.py"))
                   | set(root.glob("scripts/g3_*assessment*.py"))
                   | set(root.glob("scripts/g3_*comparison*.py"))
                   | set(root.glob("src/**/*.py")))
    if not paths or any(not path.is_file() for path in paths):
        raise ValueError("Assessment ruleset cannot be fingerprinted")
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        # A checkout on Windows may use CRLF while hosted Linux uses LF.
        # The implemented Python rule is the same in both checkouts.
        digest.update(hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).digest())
    return digest.hexdigest()


def snapshot_facts(snapshot):
    records = snapshot.get("records")
    if not isinstance(records, list) or not isinstance(snapshot.get("run_number"), int):
        raise ValueError("History input is not a model snapshot")
    models, findings = {}, {}
    for record in records:
        family, model, grade = record.get("family"), record.get("model"), record.get("grade")
        if not family or not model or grade not in GRADES:
            raise ValueError("History snapshot contains an incomplete model")
        key = (family, model)
        if key in models:
            raise ValueError("History snapshot contains duplicate exact models")
        models[key] = grade
        issues = record.get("findings")
        if not isinstance(issues, list):
            raise ValueError("History snapshot has no finding list")
        if grade == "PASS" and issues or grade != "PASS" and not issues:
            raise ValueError("History grade and finding presence differ")
        for issue in issues:
            control, code = issue.get("control"), issue.get("issue_code")
            if not control or not code:
                raise ValueError("History finding lacks control or issue code")
            finding_key = (family, model, control, code)
            if finding_key in findings:
                raise ValueError("History snapshot contains duplicate findings")
            findings[finding_key] = issue.get("severity", grade)
    normalized = {"run_number": snapshot["run_number"],
                  "models": [(family, model, grade) for (family, model), grade in sorted(models.items())],
                  "findings": [(list(key), findings[key]) for key in sorted(findings)]}
    digest = hashlib.sha256(json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return models, findings, digest


def _issue_key(row):
    return (row["family"], row["model"], row["control"], row["issue_code"])


def empty():
    return {"contract": CONTRACT, "validated_runs": [], "failed_runs": [],
            "findings": [], "events": []}


def advance(history, snapshot, source_run_id, ruleset, *, failed=False):
    """Return (updated history, current-run finding transitions)."""
    result = deepcopy(history)
    if result.get("contract") != CONTRACT:
        raise ValueError("Unsupported history contract")
    run_id = str(source_run_id)
    if not run_id or not ruleset:
        raise ValueError("A source run ID and ruleset fingerprint are required")
    if failed:
        if run_id not in {row["run_id"] for row in result["failed_runs"]}:
            result["failed_runs"].append({"run_id": run_id, "status": "FAILED"})
        return result, {name: [] for name in ("new", "resolved", "recurred", "pending_confirmation")}
    models, current, snapshot_digest = snapshot_facts(snapshot)
    observed_at = snapshot.get("built_at")
    try:
        datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ValueError("History snapshot has no valid capture timestamp") from error
    for prior in result["validated_runs"]:
        if prior["run_id"] == run_id:
            if prior["snapshot_digest"] != snapshot_digest or prior["ruleset"] != ruleset:
                raise ValueError("Same source run was replayed with different findings or rules")
            return result, {name: [] for name in ("new", "resolved", "recurred", "pending_confirmation")}
    if result["validated_runs"] and snapshot["run_number"] <= result["validated_runs"][-1]["run_number"]:
        raise ValueError("Validated history must advance by dashboard run number")
    prior_ruleset = result["validated_runs"][-1]["ruleset"] if result["validated_runs"] else ruleset
    comparable = prior_ruleset == ruleset
    previous_models = {tuple(row) for row in result["validated_runs"][-1]["population"]} if result["validated_runs"] else set()
    finding_rows = {_issue_key(row): row for row in result["findings"]}
    if len(finding_rows) != len(result["findings"]):
        raise ValueError("Stored history contains duplicate finding identities")
    transitions = {name: [] for name in ("new", "resolved", "recurred", "pending_confirmation")}
    for key in sorted(current):
        family, model, control, code = key
        row = finding_rows.get(key)
        if row is None:
            row = {"family": family, "model": model, "control": control, "issue_code": code,
                   "state": "NEW", "first_seen_at": observed_at, "first_seen_run": run_id,
                   "latest_seen_at": observed_at, "latest_seen_run": run_id,
                   "resolved_at": None, "resolved_run": None, "confirmation_candidate": None,
                   "last_observation": "PRESENT"}
            finding_rows[key] = row
            transitions["new"].append(key)
        elif row["state"] == "RESOLVED":
            row.update(state="REOPENED", latest_seen_at=observed_at,
                       latest_seen_run=run_id, resolved_at=None, resolved_run=None,
                       confirmation_candidate=None, last_observation="PRESENT")
            transitions["recurred"].append(key)
        else:
            row.update(state="OPEN", latest_seen_at=observed_at,
                       latest_seen_run=run_id, confirmation_candidate=None,
                       last_observation="PRESENT")
    for key, row in finding_rows.items():
        if key in current or row["state"] == "RESOLVED":
            continue
        if (row["family"], row["model"]) not in models:
            row["last_observation"] = "OUT_OF_SCOPE"
            row["confirmation_candidate"] = None
        elif not comparable:
            row["last_observation"] = "RULESET_CHANGED"
            row["confirmation_candidate"] = None
        elif (candidate := row.get("confirmation_candidate")) and candidate["run_id"] != run_id and candidate["ruleset"] == ruleset:
            row.update(state="RESOLVED", resolved_at=observed_at, resolved_run=run_id,
                       confirmation_candidate=None, last_observation="ABSENT_CONFIRMED")
            transitions["resolved"].append(key)
        else:
            row["confirmation_candidate"] = {"run_id": run_id, "observed_at": observed_at,
                                             "ruleset": ruleset}
            row["last_observation"] = "ABSENT_PENDING_CONFIRMATION"
            transitions["pending_confirmation"].append(key)
    result["findings"] = [finding_rows[key] for key in sorted(finding_rows)]
    population = [list(key) for key in sorted(models)]
    result["validated_runs"].append({"run_id": run_id, "run_number": snapshot["run_number"],
                                     "observed_at": observed_at, "ruleset": ruleset,
                                     "snapshot_digest": snapshot_digest, "model_count": len(models),
                                     "population": population,
                                     "scope_added": [list(key) for key in sorted(set(models) - previous_models)],
                                     "scope_removed": [list(key) for key in sorted(previous_models - set(models))]})
    for kind, keys in transitions.items():
        for key in keys:
            result["events"].append({"run_id": run_id, "observed_at": observed_at,
                                     "kind": kind.upper(), "family": key[0], "model": key[1],
                                     "control": key[2], "issue_code": key[3]})
    return result, transitions


def model_transitions(transitions, before, after):
    """Project finding events to unique model rows for the dashboard."""
    old = {(row["family"], row["model"]): row for row in before["records"]}
    new = {(row["family"], row["model"]): row for row in after["records"]}
    result = {}
    for kind, keys in transitions.items():
        grouped = {}
        for family, model, control, code in keys:
            grouped.setdefault((family, model), []).append(code)
        result[kind] = [{"family": family, "model": model,
                         "previous_grade": old.get((family, model), {}).get("grade"),
                         "grade": new.get((family, model), {}).get("grade"),
                         "issue_codes": sorted(codes)}
                        for (family, model), codes in sorted(grouped.items())]
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--ruleset", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    updated, changes = advance(read(args.history) if args.history else empty(),
                               read(args.snapshot), args.run_id, args.ruleset)
    write(args.out, updated)
    print(json.dumps({"run_id": args.run_id,
                      "transition_counts": {key: len(value) for key, value in changes.items()}},
                     ensure_ascii=False))

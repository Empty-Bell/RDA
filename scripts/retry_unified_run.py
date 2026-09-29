"""Re-run transient jobs in a completed unified audit, at most twice.

Schema, grade and report-code failures remain visible failures for review.
"""

import argparse
import json
import os
from urllib.request import Request, urlopen


FAMILIES = {
    "refrigerator", "dishwasher", "washer", "tv", "range", "cooktop",
    "dryer", "hood", "monitor", "computer", "tablet",
}


def api(path, token, *, method="GET"):
    request = Request("https://api.github.com" + path, method=method, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "RDA-unified-recovery",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(request, timeout=30) as response:
        return json.load(response) if method == "GET" else response.status


def decision(run, jobs, max_attempts):
    if (run.get("name") != "Unified 11-family full audit"
            or run.get("head_branch") != "main"
            or run.get("status") != "completed"
            or run.get("conclusion") != "failure"):
        return "not_eligible_run"
    if run.get("run_attempt", max_attempts) >= max_attempts:
        return "attempt_limit"
    failed = {job.get("name") for job in jobs if job.get("conclusion") == "failure"}
    family_failures = {name for name in failed if name and name.startswith("Acquire and assess ")}
    integrate = "Verify one source run and 11 graded populations"
    build = "Build validated Pages snapshot from this run"
    deploy = "Deploy only the validated artifact"
    public = "Confirm the public project path has this run"
    if family_failures:
        if any(name.removeprefix("Acquire and assess ") not in FAMILIES for name in family_failures):
            return "unknown_family_job"
        if failed - family_failures - {integrate}:
            return "non_source_failure"
        return "retry_family_source_failure"
    if failed == {integrate}:
        job = next(job for job in jobs if job.get("name") == integrate)
        failed_steps = {step.get("name") for step in job.get("steps", [])
                        if step.get("conclusion") == "failure"}
        if failed_steps and failed_steps <= {
            "Download family artifacts from every attempt of this run",
            "Select the latest successful attempt for each family",
        }:
            return "retry_artifact_integration"
        return "source_gate_failure"
    if failed == {build}:
        job = next(job for job in jobs if job.get("name") == build)
        failed_steps = {step.get("name") for step in job.get("steps", [])
                        if step.get("conclusion") == "failure"}
        if failed_steps and failed_steps <= {
            "Install spreadsheet export dependency", "Install browser for desktop and mobile smoke",
            "Download source artifacts from every attempt of this execution",
            "Download accepted source gate",
        }:
            return "retry_build_dependency_or_artifact"
        return "report_or_browser_code_failure"
    if failed and failed <= {deploy, public}:
        return "retry_publication_service"
    return "non_transient_failure"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise ValueError("GITHUB_TOKEN is required")
    base = f"/repos/{args.repository}/actions/runs/{args.run_id}"
    run = api(base, token)
    jobs = []
    page = 1
    while True:
        response = api(base + f"/jobs?filter=latest&per_page=100&page={page}", token)
        jobs.extend(response.get("jobs", []))
        if len(response.get("jobs", [])) < 100:
            break
        page += 1
    reason = decision(run, jobs, args.max_attempts)
    result = {"run_id": args.run_id, "run_attempt": run.get("run_attempt"), "decision": reason}
    if reason.startswith("retry_") and not args.dry_run:
        result["response_status"] = api(base + "/rerun-failed-jobs", token, method="POST")
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

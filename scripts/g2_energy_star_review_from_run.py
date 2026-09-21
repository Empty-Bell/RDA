"""Render a review-only artifact from an earlier successful source run."""

import argparse
import io
import json
import os
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from g2_energy_star_review_report import render_review_report

API = "https://api.github.com"
USER_AGENT = "RDA-Energy-Star-Review/1.0"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _api_json(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def _get_successful_run(repo: str, token: str, requested_run_id: str | None) -> dict:
    if requested_run_id:
        run = _api_json(f"{API}/repos/{repo}/actions/runs/{requested_run_id}", token)
        if (run.get("conclusion") != "success" or run.get("status") != "completed"
                or run.get("path") != ".github/workflows/g2-energy-star-source.yml"):
            raise ValueError("Requested source run is not completed successfully")
        return run
    result = _api_json(
        f"{API}/repos/{repo}/actions/workflows/g2-energy-star-source.yml/runs"
        "?branch=main&per_page=20",
        token,
    )
    runs = [run for run in result.get("workflow_runs", [])
            if run.get("status") == "completed" and run.get("conclusion") == "success"]
    if not runs:
        raise ValueError("No successful Energy Star source run is available")
    return runs[0]


def _download_assessment(repo: str, token: str, run: dict) -> dict:
    run_id = run["id"]
    artifact_list = _api_json(f"{API}/repos/{repo}/actions/runs/{run_id}/artifacts", token)
    prefix = f"g2-energy-star-source-{run_id}-"
    artifacts = [artifact for artifact in artifact_list.get("artifacts", [])
                 if artifact.get("name", "").startswith(prefix) and not artifact.get("expired")]
    if not artifacts:
        raise ValueError("Source-run artifact is missing or expired")
    artifact = sorted(artifacts, key=lambda item: item.get("created_at", ""))[-1]
    request = urllib.request.Request(artifact["archive_download_url"], headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
    })
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        opener.open(request, timeout=45)
        raise ValueError("Expected artifact archive redirect was not returned")
    except urllib.error.HTTPError as response:
        if response.code not in (301, 302, 303, 307, 308):
            raise
        location = response.headers.get("Location")
        if not location:
            raise ValueError("Artifact archive redirect has no download URL")
    with urllib.request.urlopen(location, timeout=90) as response:
        archive = response.read()
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        candidates = [name for name in zipped.namelist()
                      if PurePosixPath(name).name == "energy-star-assessment.json"]
        if len(candidates) != 1:
            raise ValueError("Artifact must contain exactly one Energy Star assessment")
        assessment = json.loads(zipped.read(candidates[0]))
        manifests = []
        for name in zipped.namelist():
            if PurePosixPath(name).name != "manifest.json":
                continue
            try:
                manifest = json.loads(zipped.read(name))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if (manifest.get("contract") == "G2_ENERGY_STAR_DIRECT_SOURCE_DECLARATIONS_V1"
                    and str(manifest.get("github_run_id")) == str(run_id)):
                manifests.append(manifest)
    if assessment.get("contract") != "G2_ENERGY_STAR_THREE_POINT_ASSESSMENT_V1":
        raise ValueError("Artifact assessment contract is invalid")
    if (len(manifests) != 1 or not assessment.get("source_run_id")
            or assessment.get("source_run_id") != manifests[0].get("run_id")):
        raise ValueError("Assessment and successful GitHub source run provenance differ")
    return assessment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", help="Successful source workflow run ID; default is latest success")
    parser.add_argument("--output", default="runtime/g2-energy-star-review/energy-star-review.md")
    args = parser.parse_args()
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GH_TOKEN"]
    run = _get_successful_run(repo, token, args.run_id)
    assessment = _download_assessment(repo, token, run)
    report = render_review_report(assessment)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write(report)
    print(json.dumps({"source_run_id": run["id"], "report": str(output)}))


if __name__ == "__main__":
    main()

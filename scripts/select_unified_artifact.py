"""Restore the latest validated gate or site from any attempt of one Actions run."""

import argparse
import json
from pathlib import Path
import re
import shutil


def select(root, kind, run_id, destination, source_sha=None):
    root, destination = Path(root), Path(destination)
    prefix = "unified-full-audit-report" if kind == "gate" else "validated-site"
    pattern = re.compile(rf"{prefix}-{re.escape(run_id)}-(\d+)$")
    choices = []
    for directory in root.iterdir():
        match = pattern.fullmatch(directory.name)
        if not match or not directory.is_dir():
            continue
        file = directory / ("unified-report.json" if kind == "gate" else "publication-manifest.json")
        if not file.is_file():
            continue
        report = json.loads(file.read_text(encoding="utf-8"))
        if str(report.get("run_id")) != run_id:
            continue
        if kind == "gate" and (report.get("execution_status") != "PASS"
                               or report.get("single_source_run") is not True):
            continue
        if kind == "site" and report.get("source_git_sha") != source_sha:
            continue
        choices.append((int(match.group(1)), directory))
    if not choices:
        raise ValueError(f"No validated {kind} artifact for run {run_id}")
    attempt, selected = max(choices)
    if destination.exists():
        raise ValueError("Artifact restore destination must be new")
    shutil.copytree(selected, destination)
    print(f"{kind}: selected run {run_id} attempt {attempt}", flush=True)
    return attempt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--kind", required=True, choices=("gate", "site"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--source-sha")
    args = parser.parse_args()
    select(args.root, args.kind, args.run_id, args.destination, args.source_sha)


if __name__ == "__main__":
    main()

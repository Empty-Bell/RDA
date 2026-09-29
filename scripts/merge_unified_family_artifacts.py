"""Restore the latest complete artifact for each family in a workflow run.

GitHub re-runs only failed jobs. Successful family artifacts therefore remain in
earlier attempts, while retried family artifacts use a newer attempt number.
"""

import argparse
import re
import shutil
from pathlib import Path


FAMILIES = (
    "refrigerator", "dishwasher", "washer", "tv", "range", "cooktop",
    "dryer", "hood", "monitor", "computer", "tablet",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-root", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    pattern = re.compile(rf"unified-family-{re.escape(args.run_id)}-(\d+)-({'|'.join(FAMILIES)})$")
    selected = {}
    for artifact in args.artifacts_root.iterdir():
        match = pattern.fullmatch(artifact.name)
        if not match or not artifact.is_dir():
            continue
        attempt, family = int(match.group(1)), match.group(2)
        manifest = artifact / "unified" / family / "unified-family-manifest.json"
        if manifest.is_file() and attempt > selected.get(family, (0, None))[0]:
            selected[family] = (attempt, artifact)
    for family in FAMILIES:
        choice = selected.get(family)
        if choice is None:
            print(f"{family}: no complete artifact; unified gate will report the missing family", flush=True)
            continue
        attempt, artifact = choice
        for source in artifact.rglob("*"):
            if not source.is_file():
                continue
            target = args.out / source.relative_to(artifact)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        print(f"{family}: selected attempt {attempt}", flush=True)


if __name__ == "__main__":
    main()

"""Create and verify an immutable, source-bound Pages publication manifest."""

import argparse
import hashlib
import json
from pathlib import Path


CONTRACT = "RDA_VALIDATED_PAGES_BUNDLE_V1"
CRITICAL = ("index.html", "app.js", "styles.css", "model-data.json",
            "history.json", "integration-manifest.json", "report-data.csv",
            "report-all-fields.csv", "report-data.xlsx")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(docs, run_id, source_sha):
    docs = Path(docs)
    model = json.loads((docs / "model-data.json").read_text(encoding="utf-8"))
    history = json.loads((docs / "history.json").read_text(encoding="utf-8"))
    integration = json.loads((docs / "integration-manifest.json").read_text(encoding="utf-8"))
    latest = history["validated_runs"][-1]
    if (str(integration.get("unified_source_run_id")) != str(run_id)
            or latest["run_id"] != str(run_id)
            or latest["run_number"] != model["run_number"]):
        raise ValueError("Pages bundle is not from the validated source run")
    files = {}
    evidence_paths = [row["evidence_url"] for row in model["records"]]
    if len(set(evidence_paths)) != len(evidence_paths):
        raise ValueError("Pages evidence path is reused across models")
    for name in CRITICAL:
        path = docs / name
        if not path.is_file():
            raise ValueError(f"Pages file missing: {name}")
        files[name] = digest(path)
    for row in model["records"]:
        path = docs / row["evidence_url"].removeprefix("./")
        if not path.is_file():
            raise ValueError(f"Evidence missing: {row['family']} {row['model']}")
        detail = json.loads(path.read_text(encoding="utf-8"))
        if detail.get("family") != row["family"] or detail.get("model") != row["model"]:
            raise ValueError(f"Evidence identity differs: {row['family']} {row['model']}")
        files[path.relative_to(docs).as_posix()] = digest(path)
    return {"contract": CONTRACT, "run_id": str(run_id), "source_git_sha": source_sha,
            "dashboard_run_number": model["run_number"], "model_count": len(model["records"]),
            "files": dict(sorted(files.items()))}


def create(docs, run_id, source_sha):
    value = inspect(docs, run_id, source_sha)
    target = Path(docs) / "publication-manifest.json"
    target.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return value


def verify(docs, run_id, source_sha):
    expected = json.loads((Path(docs) / "publication-manifest.json").read_text(encoding="utf-8"))
    actual = inspect(docs, run_id, source_sha)
    if expected != actual:
        raise ValueError("Validated Pages bundle hash or source identity differs")
    return actual


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("create", "verify"))
    parser.add_argument("--docs", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    value = (create if args.mode == "create" else verify)(args.docs, args.run_id, args.source_sha)
    print(json.dumps({"status": "PASS", "run_id": value["run_id"],
                      "dashboard_run_number": value["dashboard_run_number"],
                      "hashed_files": len(value["files"])}, ensure_ascii=False))

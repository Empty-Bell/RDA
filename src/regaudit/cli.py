"""Offline draft CLI: validate envelopes or create an unevaluated skeleton."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid
from .contracts import validate_bundle, verify_evidence_files, dumps
from .config import load_configuration
from .report import summarize_bundle


def configuration(root: Path) -> str:
    return load_configuration(root)[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("bundle", type=Path)
    validate.add_argument("--evidence-root", type=Path, required=True)
    summary = commands.add_parser("summarize")
    summary.add_argument("bundle", type=Path)
    summary.add_argument("--evidence-root", type=Path, required=True)
    summary.add_argument("--output", type=Path, required=True)
    init = commands.add_parser("init-run")
    init.add_argument("--git-sha", required=True)
    init.add_argument("--project", type=Path, default=Path.cwd())
    init.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in ("validate", "summarize"):
            bundle = validate_bundle(json.loads(args.bundle.read_bytes()))
            verify_evidence_files(bundle, args.evidence_root)
            if args.command == "summarize":
                result = summarize_bundle(bundle)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(dumps(result))
                print("CREATED_UNEVALUATED_SUMMARY")
                return 0
            print("VALID_DRAFT_BUNDLE")
            return 0
        now = datetime.now(timezone.utc).isoformat()
        config, config_hash = load_configuration(args.project)
        bundle = {
            "manifest": {
                "schema_version": "draft-1",
                "run_id": uuid.uuid4().hex,
                "started_at": now,
                "completed_at": None,
                "git_sha": args.git_sha,
                "config_hash": config_hash,
                "rule_version": None,
                "source_contract_version": config["sources"]["contract_version"],
                "python_version": sys.version.split()[0],
                "playwright_version": None,
                "runner": "offline-skeleton",
                "overall_execution_status": "OUTPUT_MISSING",
                "assessment_enabled": False,
            },
            "products": [],
            "facts": [],
            "evidence": [],
            "assessments": [],
        }
        validate_bundle(bundle)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(dumps(bundle))
        print("CREATED_UNEVALUATED_SKELETON")
        return 0
    except (ValueError, TypeError, KeyError, OSError) as error:
        print("DRAFT_CONTRACT_ERROR: " + type(error).__name__, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

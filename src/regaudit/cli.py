"""Offline draft CLI: validate envelopes or create an unevaluated skeleton."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import uuid
from .contracts import validate_bundle, verify_evidence_files, dumps, ContractError


def configuration(root):
    names = ('families', 'sources', 'controls', 'presentation', 'runtime')
    content = {name: json.loads((root / 'configs' / (name + '.yaml')).read_bytes()) for name in names}
    if (content['controls'].get('assessment_enabled') is not False
            or content['controls'].get('rule_version') is not None
            or content['presentation'].get('enabled') is not False):
        raise ContractError('Unapproved assessment configuration')
    canonical = json.dumps(content, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(canonical).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    validate = commands.add_parser('validate'); validate.add_argument('bundle', type=Path)
    validate.add_argument('--evidence-root', type=Path, required=True)
    init = commands.add_parser('init-run'); init.add_argument('--git-sha', required=True)
    init.add_argument('--project', type=Path, default=Path.cwd()); init.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'validate':
            bundle = validate_bundle(json.loads(args.bundle.read_bytes()))
            verify_evidence_files(bundle, args.evidence_root)
            print('VALID_DRAFT_BUNDLE'); return 0
        now = datetime.now(timezone.utc).isoformat()
        bundle = {'manifest': {'schema_version': 'draft-1', 'run_id': uuid.uuid4().hex, 'started_at': now,
            'completed_at': None, 'git_sha': args.git_sha, 'config_hash': configuration(args.project),
            'rule_version': None, 'source_contract_version': 'g0-2026-09-17',
            'python_version': sys.version.split()[0], 'playwright_version': None,
            'runner': 'offline-skeleton', 'overall_execution_status': 'OUTPUT_MISSING', 'assessment_enabled': False},
            'products': [], 'facts': [], 'evidence': [], 'assessments': []}
        validate_bundle(bundle)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8', newline='\n') as stream: stream.write(dumps(bundle))
        print('CREATED_UNEVALUATED_SKELETON'); return 0
    except (ValueError, TypeError, KeyError, OSError) as error:
        print('DRAFT_CONTRACT_ERROR: ' + type(error).__name__, file=sys.stderr); return 1


if __name__ == '__main__': raise SystemExit(main())

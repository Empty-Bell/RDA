"""Verify repository fixture bytes; this check cannot promote the G0 phase gate."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def review(root, git_blobs=False):
    checks = []

    def check(name, expected, manifest):
        path = root / name
        if not name.startswith('tests/fixtures/') or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'Unsafe fixture path: {name}')
        data = subprocess.run(['git', 'show', f'HEAD:{name}'], cwd=root,
                              capture_output=True, check=True).stdout if git_blobs else path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        checks.append({'manifest': manifest, 'fixture': name, 'sha256': actual,
                       'status': 'PASS' if actual == expected else 'FAIL'})

    def walk(value, manifest):
        if isinstance(value, dict):
            name = value.get('file', value.get('fixture'))
            expected = value.get('sha256', value.get('fixture_sha256'))
            if name and expected:
                check(name, expected, manifest)
            if 'projected_fixture' in value:
                check(value['projected_fixture'], value['projected_sha256'], manifest)
            for item in value.values():
                walk(item, manifest)
        elif isinstance(value, list):
            for item in value:
                walk(item, manifest)

    for path in sorted((root / 'docs/evidence').glob('*fixture-manifest.json')):
        walk(json.loads(path.read_text(encoding='utf-8')), path.name)
    if not checks:
        raise ValueError('No fixture checks discovered')
    return {'status': 'PASS' if all(x['status'] == 'PASS' for x in checks) else 'FAIL',
            'scope': 'repository fixture path and byte integrity only',
            'phase_gate': 'NOT_EVALUATED', 'compliance': 'NOT_EVALUATED',
            'byte_source': 'HEAD blobs' if git_blobs else 'checkout files', 'checks': checks}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--git-blobs', action='store_true', help='Local CRLF checkout diagnostic only')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / 'runtime/g0-review.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {'status': 'FAIL', 'phase_gate': 'NOT_EVALUATED', 'compliance': 'NOT_EVALUATED'}
    try:
        result = review(root, args.git_blobs)
    finally:
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'checks'}))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)

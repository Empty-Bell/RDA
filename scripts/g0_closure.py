"""Combined repository replay checkpoint; reviewer assigns the phase gate."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.g0_evidence_review import review


def main():
    output = ROOT / 'runtime/g0-closure.json'; output.parent.mkdir(parents=True, exist_ok=True)
    report = {'status': 'FAIL', 'phase_gate': 'NOT_EVALUATED', 'compliance': 'NOT_EVALUATED',
              'scope': 'combined fixture contracts and recorded evidence consistency; not a new live scan',
              'run_id': os.getenv('GITHUB_RUN_ID'), 'git_sha': os.getenv('GITHUB_SHA')}
    try:
        integrity = review(ROOT)
        if integrity['status'] != 'PASS': raise ValueError('Fixture hash verification failed')
        report['fixture_references'] = len(integrity['checks'])
        loader = unittest.TestLoader()
        suite = unittest.TestSuite([loader.discover(str(ROOT / 'tests')),
            loader.loadTestsFromNames(['scripts.epa_routing_test', 'scripts.applicability_test', 'scripts.g0_closure_test'])])
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        report['tests'] = {'run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                          'skipped': [{'test': test.id(), 'reason': reason} for test, reason in result.skipped]}
        if not result.wasSuccessful(): raise ValueError('Combined contract replay failed')
        if any(reason != 'Hosted bootstrap provides OpenCV' for _, reason in result.skipped) or len(result.skipped) > 1:
            raise ValueError('Unexpected skipped contract')
        evidence = {}
        for name in ('runtime-freeze-recon.json', 'epa-query-recon.json', 'epa-routing-recon.json', 'applicability-recon.json'):
            path = ROOT / 'docs/evidence' / name; raw = path.read_bytes(); data = json.loads(raw)
            if data.get('status') != 'PASS': raise ValueError('Recorded evidence not PASS: ' + name)
            evidence[name] = {'sha256': hashlib.sha256(raw).hexdigest(),
                              'status': data['status'], 'code_commit': data.get('code_commit', data.get('git_sha'))}
        report['recorded_evidence'] = evidence
        report['status'] = 'PASS'
    finally:
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'recorded_evidence'}))


if __name__ == '__main__': main()

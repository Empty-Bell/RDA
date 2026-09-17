"""Persist fixture execution evidence even when tests fail."""
import json
import os
from pathlib import Path
import platform
import sys
import unittest

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'src'))
suite = unittest.defaultTestLoader.discover(str(root / 'checks/g1'), pattern='test_*.py')
result = unittest.TextTestRunner(verbosity=2).run(suite)
report = {'scope':'G1 draft foundation fixtures; not compliance evaluation',
          'status':'PASS' if result.wasSuccessful() and not result.skipped else 'FAIL',
          'phase_gate':'NOT_EVALUATED', 'python':platform.python_version(),
          'platform':platform.platform(), 'architecture':platform.machine(),
          'run_id':os.getenv('GITHUB_RUN_ID'), 'run_attempt':os.getenv('GITHUB_RUN_ATTEMPT'),
          'git_sha':os.getenv('GITHUB_SHA'), 'tests':result.testsRun,
          'failures':len(result.failures), 'errors':len(result.errors),
          'skipped':[{'test':str(test),'reason':reason} for test,reason in result.skipped]}
output = root / 'runtime/g1' / ('fixture-' + platform.python_version() + '.json')
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['status']=='PASS' else 1)

"""Pinned static checks and installed wheel CLI from outside the source tree."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'runtime/g1'
OUT.mkdir(parents=True, exist_ok=True)
report = {'scope':'G1 static and installed CLI checks', 'status':'FAILED',
          'phase_gate':'NOT_EVALUATED', 'python':platform.python_version(),
          'run_id':os.getenv('GITHUB_RUN_ID'), 'run_attempt':os.getenv('GITHUB_RUN_ATTEMPT'),
          'git_sha':os.getenv('GITHUB_SHA'), 'checks':[],
          'tool_lock_sha256':hashlib.sha256((ROOT/'requirements-g1-tools.lock').read_bytes()).hexdigest()}


def command(name, args, *, cwd=ROOT, expected=0, env=None):
    result = subprocess.run([str(x) for x in args],cwd=cwd,env=env,
                            capture_output=True,text=True,timeout=120)
    report['checks'].append({'name':name,'status':'PASS' if result.returncode==expected else 'FAIL',
                             'exit_code':result.returncode,'expected_exit_code':expected,
                             'output_sha256':hashlib.sha256((result.stdout+result.stderr).encode()).hexdigest()})
    if result.returncode!=expected:
        print(result.stdout);print(result.stderr)
        raise RuntimeError(name+' failed')
    return result.stdout


try:
    names=('ruff','mypy','setuptools','wheel','packaging','typing_extensions',
           'mypy_extensions','pathspec','librt','ast_serialize')
    report['tools']={name:importlib.metadata.version(name) for name in names}
    command('lint',[sys.executable,'-m','ruff','check','src/regaudit'])
    command('format',[sys.executable,'-m','ruff','format','--check','src/regaudit'])
    command('types',[sys.executable,'-m','mypy','--no-incremental'])
    wheels=OUT/'wheels';wheels.mkdir(exist_ok=True)
    command('build-wheel',[sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation','.',
                           '--wheel-dir',wheels])
    wheel=wheels/'regaudit-0.1.0-py3-none-any.whl'
    report['wheel_sha256']=hashlib.sha256(wheel.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory() as temp:
        temp=Path(temp);venv=temp/'installed'
        command('isolated-environment',[sys.executable,'-m','venv',venv])
        binary=venv/('Scripts' if os.name=='nt' else 'bin')
        python=binary/('python.exe' if os.name=='nt' else 'python')
        cli=binary/('regaudit.exe' if os.name=='nt' else 'regaudit')
        env=os.environ.copy();env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
        command('install-wheel',[python,'-m','pip','install','--no-index','--no-deps',wheel],cwd=temp,env=env)
        location=command('installed-import',[python,'-c','import regaudit; print(regaudit.__file__)'],cwd=temp,env=env).strip()
        if not Path(location).resolve().is_relative_to(venv.resolve()):raise RuntimeError('Import escaped installed environment')
        command('entrypoint-help',[cli,'--help'],cwd=temp,env=env)
        fixture=ROOT/'fixtures/g1';bundle=fixture/'typed-bundle.json'
        command('validate-typed-fixture',[cli,'validate',bundle,'--evidence-root',fixture],cwd=temp,env=env)
        command('missing-evidence-rejected',[cli,'validate',bundle,'--evidence-root',temp],cwd=temp,env=env,expected=1)
        summary=temp/'summary.json'
        command('summary',[cli,'summarize',bundle,'--evidence-root',fixture,'--output',summary],cwd=temp,env=env)
        before=summary.read_bytes()
        command('summary-overwrite-rejected',[cli,'summarize',bundle,'--evidence-root',fixture,'--output',summary],cwd=temp,env=env,expected=1)
        if summary.read_bytes()!=before:raise RuntimeError('Summary overwritten')
        snapshots=[]
        for number in range(2):
            output=temp/('run-'+str(number)+'.json')
            args=[cli,'init-run','--git-sha','0'*40,'--project',ROOT,'--output',output]
            command('init-run-'+str(number),args,cwd=temp,env=env)
            snapshots.append(json.loads(output.read_bytes()))
        if snapshots[0]['manifest']['run_id']==snapshots[1]['manifest']['run_id']:raise RuntimeError('Run identity reused')
        if any(s['manifest']['overall_execution_status']!='OUTPUT_MISSING' or s['manifest']['assessment_enabled'] is not False for s in snapshots):raise RuntimeError('Skeleton implied evaluation')
        original=output.read_bytes()
        command('run-overwrite-rejected',args,cwd=temp,env=env,expected=1)
        if output.read_bytes()!=original:raise RuntimeError('Run overwritten')
    report['status']='PASS'
except Exception as error:
    report['error_class']=type(error).__name__
    print('G1_QUALITY_FAILED: '+str(error),file=sys.stderr)
finally:
    (OUT/('quality-'+platform.python_version()+'.json')).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['status']=='PASS' else 1)

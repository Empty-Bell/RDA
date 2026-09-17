"""Fail-closed runtime resource gate; controlled recovery uses isolated copies."""
import argparse
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
import os
import platform
import re
import shutil
import urllib.request
from pathlib import Path


def safe_path(root, relative):
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('Resource path escapes package')
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Resource path escapes package')
    return target


def inspect_files(root, records):
    seen = set(); observations = []
    for record in records:
        if record['path'] in seen or not re.fullmatch(r'[0-9a-f]{64}',record['sha256']):
            raise ValueError('Invalid or duplicated resource manifest')
        seen.add(record['path'])
        path = safe_path(root,record['path'])
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        observations.append({'path':record['path'],'expected_sha256':record['sha256'],'actual_sha256':actual,
                             'status':'PASS' if actual == record['sha256'] else 'FAIL'})
    return observations


def require_integrity(observations):
    if not observations or any(r['status'] != 'PASS' for r in observations):
        raise ValueError('Runtime resources missing or hash mismatch; source collection blocked')


def prepare_models(root, records, output):
    for record in records:
        target = safe_path(root,record['path'])
        if target.exists():
            continue  # Wrong existing bytes fail verification, never silently replaced.
        urls = record.get('download_url_candidates',[])
        if not record['path'].endswith('.onnx') or len(urls) != 1 or not urls[0].startswith('https://'):
            raise ValueError('Missing resource has no unique pinned HTTPS source')
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary = target.with_name(target.name + '.download')
        with urllib.request.urlopen(urls[0],timeout=60) as response, temporary.open('wb') as stream:
            while chunk := response.read(1024*1024): stream.write(chunk)
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        if digest != record['sha256']:
            shutil.copyfile(temporary,output / (target.name + '-rejected.bin'))
            raise ValueError('Downloaded model hash differs; raw rejected bytes retained')
        temporary.replace(target)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','verify','recovery'])
    mode=parser.parse_args().mode
    output=Path('runtime/integrity');output.mkdir(parents=True,exist_ok=True)
    report={'status':'RUNNING','mode':mode,'run_id':os.getenv('GITHUB_RUN_ID'),
            'git_sha':os.getenv('GITHUB_SHA'),'runner_image':os.getenv('ImageOS'),
            'runner_image_version':os.getenv('ImageVersion'),'python':platform.python_version(),
            'platform':platform.platform(),'compliance':'NOT_EVALUATED'}
    def save(name,data):(output / name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    save(mode+'.json',report)
    try:
        manifest_path=Path('runtime-manifest.json')
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        for file,key in [('requirements-probe.lock','requirements_probe_sha256'),('requirements-tools.lock','requirements_tools_sha256')]:
            assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==manifest[key], 'Lockfile hash drifted'
        report['manifest_sha256']=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        assert platform.python_version()==manifest['python'] and platform.system()=='Linux' and platform.machine()=='x86_64', 'Unsupported locked runtime target'
        assert 'VERSION_ID="24.04"' in Path('/etc/os-release').read_text(), 'Ubuntu 24.04 target required'
        installed={re.sub(r'[-_.]+','-',d.metadata['Name']).lower():d.version for d in metadata.distributions()}
        report['package_versions']={n:installed.get(n) for n in manifest['packages']}
        assert report['package_versions']==manifest['packages'], 'Locked package versions drifted'
        root=Path(next(iter(importlib.util.find_spec('rapidocr').submodule_search_locations)))
        records=manifest['ocr_files']
        if mode=='prepare':prepare_models(root,records,output)
        report['resources']=inspect_files(root,records);save(mode+'.json',report)
        require_integrity(report['resources'])
        actual_models={p.relative_to(root).as_posix() for p in root.rglob('*.onnx')}
        assert actual_models=={r['path'] for r in records if r['path'].endswith('.onnx')}, 'Unexpected OCR model resource'
        import playwright
        registry=Path(playwright.__file__).parent / 'driver/package/browsers.json'
        report['browser_registry_canonical_sha256']=hashlib.sha256(json.dumps(json.loads(registry.read_text()),sort_keys=True).encode()).hexdigest()
        assert report['browser_registry_canonical_sha256']==manifest['browser_registry_canonical_sha256'], 'Browser revision registry drifted'
        if mode=='recovery':
            shadow=output / 'controlled-model-copy';shadow.mkdir(exist_ok=True)
            for r in records:
                destination=safe_path(shadow,r['path']);destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(safe_path(root,r['path']),destination)
            model=next(r for r in records if r['path'].endswith('.onnx'))
            target=safe_path(shadow,model['path'])
            with target.open('ab') as stream:stream.write(b'CONTROLLED_CORRUPTION')
            failed=inspect_files(shadow,records);save('controlled-corruption.json',{'status':'FAIL','resources':failed})
            shutil.copyfile(target,output / 'controlled-corrupt-model.bin')
            try:require_integrity(failed)
            except ValueError:report['controlled_corruption_gate']='EXPECTED_FAILURE_BLOCKED'
            else:raise AssertionError('Corrupted copy accepted')
            # Original verified package remains intact; recovery reuses trusted bytes.
            source=safe_path(root,model['path'])
            assert hashlib.sha256(source.read_bytes()).hexdigest()==model['sha256']
            shutil.copyfile(source,target)
            recovered=inspect_files(shadow,records);require_integrity(recovered)
            save('controlled-recovered.json',{'status':'PASS','resources':recovered})
            report['controlled_recovery']='VERIFIED_COPY_RESTORED_NO_COMPLIANCE_DECISION'
            # Only generated, individually checked temporary copies are removed;
            # corruption bytes and all before/after observations remain artifacts.
            for r in records:safe_path(shadow,r['path']).unlink()
        report['status']='PASS';save(mode+'.json',report)
        print(json.dumps({'mode':mode,'status':report['status'],'resources':len(records)}))
    except Exception as error:
        report['status']='FAIL';report['error']={'type':type(error).__name__,'message':str(error)}
        save(mode+'.json',report);raise


if __name__=='__main__':main()

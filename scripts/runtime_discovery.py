"""One-off hosted inventory; emits proposed locks, never silently updates them."""
import hashlib
import importlib.metadata as metadata
import json
import platform
import re
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

OUT = Path('runtime/freeze-discovery')


def pypi(name, version=None):
    url = 'https://pypi.org/pypi/' + name + ('/' + version if version else '') + '/json'
    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.load(response)
    assert data['urls'] and all(f['digests']['sha256'] for f in data['urls'])
    return data


def lock(path, versions):
    lines = ['# Proposed from observed hosted environment; reviewed before use.']
    evidence = []
    for name, version in sorted(versions.items()):
        release = pypi(name, version)
        hashes = sorted({f['digests']['sha256'] for f in release['urls']})
        lines.append(name + '==' + version + ' \\\n' + ' \\\n'.join('    --hash=sha256:' + h for h in hashes))
        evidence.append({'name':name,'version':version,'release_files':len(hashes),
                         'sdist_only':all(f['packagetype']=='sdist' for f in release['urls'])})
    (OUT / path).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return evidence


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report = {'status':'RUNNING','python':platform.python_version(),'platform':platform.platform()}
    def save(): (OUT / 'inventory.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    save()
    try:
        installed = {re.sub(r'[-_.]+','-',d.metadata['Name']).lower():d.version for d in metadata.distributions()}
        tools = {'pip':installed['pip']}
        for name in ('setuptools','wheel'):
            tools[name] = installed.get(name) or pypi(name)['info']['version']
        tools['packaging'] = installed['packaging']
        runtime = {n:v for n,v in installed.items() if n not in ('pip','setuptools','wheel')}
        report['runtime_packages'] = lock('requirements-probe.lock',runtime)
        report['build_tools'] = lock('requirements-tools.lock',tools)
        import cv2, rapidocr, yaml
        from rapidocr import RapidOCR
        cv2.setNumThreads(1)
        RapidOCR(params={'EngineConfig.onnxruntime.intra_op_num_threads':1,
                         'EngineConfig.onnxruntime.inter_op_num_threads':1})
        root = Path(rapidocr.__file__).parent
        urls = []
        def walk(value):
            if isinstance(value,dict):
                for item in value.values(): walk(item)
            elif isinstance(value,list):
                for item in value: walk(item)
            elif isinstance(value,str) and value.startswith('https://'): urls.append(value)
        for path in root.rglob('*.yaml'):
            walk(yaml.safe_load(path.read_text(encoding='utf-8')))
        files = []
        for path in sorted(root.rglob('*')):
            if path.is_file() and path.suffix in ('.onnx','.txt','.yaml'):
                matches = sorted({u for u in urls if Path(urlsplit(u).path).name == path.name})
                files.append({'path':path.relative_to(root).as_posix(), 'size_bytes':path.stat().st_size,
                              'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'download_url_candidates':matches})
        assert sum(f['path'].endswith('.onnx') for f in files) >= 3, 'OCR model inventory incomplete'
        report['ocr'] = {'package_version':metadata.version('rapidocr'),'files':files}
        import playwright
        browsers = Path(playwright.__file__).parent / 'driver/package/browsers.json'
        report['playwright_browsers'] = json.loads(browsers.read_text(encoding='utf-8'))
        report['status'] = 'PASS';save()
        print(json.dumps({'runtime_packages':len(runtime),'tools':tools,'ocr_files':files}))
    except Exception as error:
        report['status']='FAIL';report['error']={'type':type(error).__name__,'message':str(error)};save();raise


if __name__ == '__main__': main()

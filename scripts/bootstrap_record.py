"""Minimal bootstrap stage evidence, including early install failures."""
import json,os,sys
from datetime import datetime,timezone
from pathlib import Path

root=Path('runtime');root.mkdir(exist_ok=True);path=root/'bootstrap.json'
stage=sys.argv[1];code=int(sys.argv[2])
data=json.loads(path.read_text()) if path.exists() and stage!='begin' else {
    'status':'RUNNING','run_id':os.getenv('GITHUB_RUN_ID'),'git_sha':os.getenv('GITHUB_SHA'),'stages':[]}
data['stages'].append({'stage':stage,'exit_code':code,'at':datetime.now(timezone.utc).isoformat()})
data['status']='FAIL' if code else 'PASS' if stage=='complete' else 'RUNNING'
path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

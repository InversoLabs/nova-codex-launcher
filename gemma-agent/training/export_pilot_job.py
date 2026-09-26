"""Bounded CPU merge with restoration of the originally loaded Ollama model."""
import json
import os
import subprocess
import sys
from pathlib import Path
from run_pilot_job import request,ensure_idle

root=Path(__file__).resolve().parents[1]
out=root/'runs/export-pilot-v1'; out.mkdir(exist_ok=False)
cfg=json.loads((root/'training/gemma-e2b.json').read_text())
ensure_idle(request('http://127.0.0.1:18183/api/projects'))
models=request('http://127.0.0.1:11434/api/ps')['models']
if any(m['name']!='gpt-oss:20b' for m in models): raise RuntimeError('Another model is active')
original=next(iter(models),None)
state={'success':False,'restored':None}
try:
    if original: request('http://127.0.0.1:11434/api/generate',{'model':original['name'],'keep_alive':0},60)
    with (out/'merge.log').open('w') as log:
        proc=subprocess.Popen([str(root/'.venv-training/Scripts/python.exe'),'-u',str(root/'training/merge_export.py'),
            '--base',str(root/'models'/cfg['revision']),'--revision',cfg['revision'],
            '--adapter',str(root/'runs/real-pilot-v2/training/adapter'),'--out',str(out/'export'),'--execute'],
            stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},
            creationflags=subprocess.CREATE_NO_WINDOW)
        try: code=proc.wait(timeout=1200)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True); raise
    if code: raise RuntimeError('Merge failed; inspect merge.log')
    state['success']=True
except Exception as exc: state['error']=str(exc)
finally:
    if original:
        try:
            request('http://127.0.0.1:11434/api/generate',{'model':original['name'],'prompt':'','stream':False,'keep_alive':-1,
                'options':{'num_ctx':original.get('context_length',8192),'num_predict':1}},300)
            state['restored']=any(m['name']==original['name'] for m in request('http://127.0.0.1:11434/api/ps')['models'])
        except Exception as exc: state['restore_error']=str(exc); state['restored']=False
    (out/'result.json').write_text(json.dumps(state,indent=2)); print(json.dumps(state),flush=True)

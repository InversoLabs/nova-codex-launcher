"""Run one bounded pilot, restoring the originally resident GPT-OSS in finally."""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

def request(url,payload=None,timeout=15):
    req=urllib.request.Request(url,data=None if payload is None else json.dumps(payload).encode(),
                               headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as response: return json.load(response)

def ensure_idle(projects):
    if not isinstance(projects,list): raise ValueError('Unrecognized Conductor project inventory')
    if any(p.get('status') not in ('COMPLETE','NEEDS_ATTENTION','STOPPED') for p in projects):
        raise RuntimeError('Conductor has active work; leave production model alone')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--out',required=True); args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    out=(root/args.out).resolve(); out.mkdir(parents=True,exist_ok=False)
    cfg=json.loads((root/'training/gemma-e2b.json').read_text())
    base=root/'models'/cfg['revision']
    if not (base/'weight-integrity.json').is_file(): raise RuntimeError('Verified weights are not ready')
    state={'phase':'preflight','started':time.time(),'training_success':False,'restored':None}
    environment={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    def update(**values):
        state.update(values); (out/'job.json').write_text(json.dumps(state,indent=2)); print(json.dumps(state),flush=True)
    ensure_idle(request('http://127.0.0.1:18183/api/projects'))
    models=request('http://127.0.0.1:11434/api/ps')['models']
    original=next((m for m in models if m['name']=='gpt-oss:20b'),None)
    if any(m['name']!='gpt-oss:20b' for m in models): raise RuntimeError('Other resident model detected; do not compete for its memory')
    try:
        if original:
            update(phase='unloading_authorized_model')
            request('http://127.0.0.1:11434/api/generate',{'model':'gpt-oss:20b','keep_alive':0},60)
        update(phase='backend_preflight')
        with (out/'backend.log').open('w',encoding='utf-8') as log:
            probe=subprocess.Popen([str(root/'.venv-training/Scripts/python.exe'),'-u',
                str(root/'training/backend_probe.py'),'--allow-backend-probe'],cwd=root,
                stdout=log,stderr=subprocess.STDOUT,env=environment,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try: probe_code=probe.wait(timeout=180)
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill','/PID',str(probe.pid),'/T','/F'],capture_output=True)
                probe.wait(timeout=20); raise RuntimeError('Backend preflight timed out')
        backend=json.loads((root/'runs/backend-probe.json').read_text())
        if probe_code or not all(backend.get(k,{}).get('passed') for k in
                ('kv_shared_training_parity','tiny_gemma_lora','nf4','hybrid_cpu_embeddings')):
            raise RuntimeError('Backend preflight failed; inspect backend.log')
        command=[str(root/'.venv-training/Scripts/python.exe'),'-u',str(root/'training/pilot.py'),
                 '--base',str(base),'--data',str(root/'datasets/gpt-teacher-seed'),
                 '--out',str(out/'training'),'--steps','2','--execute']
        with (out/'training.log').open('w',encoding='utf-8') as log:
            child=subprocess.Popen(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,env=environment,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            update(phase='training_pilot',pid=child.pid)
            try: code=child.wait(timeout=1200)
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True)
                child.wait(timeout=20); raise RuntimeError('Pilot exceeded 20 minute limit')
        report=json.loads((out/'training/pilot-report.json').read_text()) if (out/'training/pilot-report.json').exists() else {}
        if code!=0 or not report.get('success'): raise RuntimeError('Pilot failed; inspect training.log and pilot-report.json')
        update(training_success=True)
    except Exception as exc:
        update(error=type(exc).__name__+': '+str(exc))
    finally:
        if original:
            update(phase='restoring_original_model')
            try:
                request('http://127.0.0.1:11434/api/generate',{'model':'gpt-oss:20b','prompt':'','stream':False,
                    'keep_alive':-1,'options':{'num_ctx':original.get('context_length',8192),'num_predict':1}},300)
                restored=request('http://127.0.0.1:11434/api/ps')['models']
                update(restored=any(m['name']=='gpt-oss:20b' for m in restored))
            except Exception as exc: update(restored=False,restore_error=str(exc))
        try: state['conductor_health']=request('http://127.0.0.1:18183/health',timeout=8)
        except Exception as exc: state['health_error']=str(exc)
        update(phase='complete' if state['training_success'] and state['restored'] is not False else 'failed',finished=time.time())
    if state['phase']!='complete': sys.exit(1)

if __name__=='__main__': main()

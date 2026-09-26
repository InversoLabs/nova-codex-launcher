"""Own one isolated, low-priority llama.cpp process; never touch production PIDs."""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
HOME=Path.home()
EXE=HOME/'NOVA-Agent/llama.cpp/llama-server.exe'

def request(url,payload=None):
    req=urllib.request.Request(url,data=None if payload is None else json.dumps(payload).encode(),
                               headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as r: return json.load(r)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--tag',default='e2b-it-qat')
    p.add_argument('--port',type=int,default=18190); p.add_argument('--out',required=True)
    p.add_argument('--evaluate',action='store_true'); p.add_argument('--task')
    p.add_argument('--threads',type=int,default=2); p.add_argument('--hold',type=int,default=0)
    p.add_argument('--mode',choices=['cpu','shared-gpu','gpu','single-gpu'],default='cpu')
    p.add_argument('--context',type=int,default=4096)
    p.add_argument('--native-compact',action='store_true')
    p.add_argument('--native-tasks',default='clamp')
    args=p.parse_args()
    if args.tag not in ('e2b-it-qat','e2b'): raise ValueError('Unsupported tag')
    out=ROOT/args.out; out.mkdir(parents=True,exist_ok=False)
    manifest_path=HOME/'.ollama/models/manifests/registry.ollama.ai/library/gemma4'/args.tag
    manifest=json.loads(manifest_path.read_text())
    model=next(x for x in manifest['layers'] if x['mediaType']=='application/vnd.ollama.image.model')
    blob=HOME/'.ollama/models/blobs'/model['digest'].replace(':','-')
    with socket.socket() as s:
        s.bind(('127.0.0.1',args.port))
    cmd=[str(EXE),'-m',str(blob),'--host','127.0.0.1','--port',str(args.port),
         '-c',str(args.context),'-np','1','-t',str(args.threads),'-tb',str(args.threads),
         '--reasoning','off','--no-warmup','--alias','gemma-e2b-lab','--poll','0','-ub','128']
    env={k:v for k,v in os.environ.items() if not k.startswith('LLAMA_ARG_')}
    if args.mode=='cpu':
        cmd+=['-ngl','0','--fit','off']; env['CUDA_VISIBLE_DEVICES']='-1'
    elif args.mode=='shared-gpu':
        cmd+=['--fit','on','--fit-target','1024,1024','-ot','per_layer_token_embd.weight=CPU']
        env.pop('CUDA_VISIBLE_DEVICES',None)
    else:
        cmd+=['-ngl','99','--fit','off','-ot','per_layer_token_embd.weight=CPU','-ts','1,1','--load-mode','none']
        env.pop('CUDA_VISIBLE_DEVICES',None)
        if args.mode=='single-gpu':
            cmd+=['--device','CUDA1','--split-mode','none','--main-gpu','0']
    flags=(subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS) if os.name=='nt' else 0
    metadata={'command':cmd,'model_digest':model['digest'],'model_bytes':model['size'],
              'mode':args.mode+' text-only','started':time.time()}
    (out/'session.json').write_text(json.dumps(metadata,indent=2))
    log=(out/'server.log').open('w',encoding='utf-8')
    proc=subprocess.Popen(cmd,cwd=EXE.parent,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=flags)
    (out/'server.pid').write_text(str(proc.pid))
    base=f'http://127.0.0.1:{args.port}'
    try:
        for _ in range(120):
            if proc.poll() is not None: raise RuntimeError(f'Lab server exited {proc.returncode}; see {out}/server.log')
            try:
                if request(base+'/health').get('status')=='ok': break
            except Exception: pass
            time.sleep(1)
        else: raise RuntimeError('Lab server readiness timeout')
        print('LAB_READY '+str(proc.pid),flush=True)
        probes=[]
        for i in range(2):
            started=time.monotonic()
            r=request(base+'/v1/chat/completions',{'model':'gemma-e2b-lab','messages':[{'role':'user','content':'Reply with only READY.'}],
                'max_tokens':24,'temperature':0,'chat_template_kwargs':{'enable_thinking':False}})
            probes.append({'seconds':time.monotonic()-started,'response':r})
        (out/'probes.json').write_text(json.dumps(probes,indent=2))
        print(json.dumps(probes),flush=True)
        try:
            response_probe=request(base+'/v1/responses',{'model':'gemma-e2b-lab','input':'Reply with only READY.','max_output_tokens':16,'stream':False})
        except Exception as exc: response_probe={'error':str(exc)}
        (out/'responses-probe.json').write_text(json.dumps(response_probe,indent=2))
        if args.evaluate:
            cmd=[sys.executable,'-m','lab','evaluate','--model','gemma-e2b-lab','--url',base+'/v1','--out',str(out/'evaluation'),'--steps','6']
            if args.task: cmd+=['--task',args.task]
            subprocess.run(cmd,cwd=ROOT,check=True,creationflags=flags)
        if args.native_compact:
            native_results=[]
            for task_id in args.native_tasks.split(','):
                from lab.tasks import get
                get(task_id)
                target=out/('native-codex-'+task_id)
                subprocess.run([sys.executable,str(ROOT/'native_codex.py'),'--compact','--context',str(args.context),
                                '--task',task_id,'--timeout','180','--out',str(target)],cwd=ROOT,check=True,creationflags=flags,timeout=240)
                native_results.append(json.loads((target/'result.json').read_text()))
            (out/'native-summary.json').write_text(json.dumps(native_results,indent=2))
        if args.hold: time.sleep(args.hold)
    finally:
        proc.terminate()
        try: proc.wait(timeout=15)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=15)
        log.close()
        (out/'stopped.json').write_text(json.dumps({'pid':proc.pid,'returncode':proc.returncode,'stopped':time.time()}))

if __name__=='__main__': main()

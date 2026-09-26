"""Real Codex smoke run with a private home/catalog and the existing read-only proxy.

No production provider, home, config, schedule or service is changed.
"""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from lab.safe_python import run
from lab import tasks

ROOT=Path(__file__).resolve().parent
STUDIO=Path.home()/'Documents/Nova Conductor Studio'
CODEX=STUDIO/'runtime/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe'

def main():
    p=argparse.ArgumentParser(); p.add_argument('--out',required=True)
    p.add_argument('--url',default='http://127.0.0.1:18190/v1')
    p.add_argument('--model',default='gemma-e2b-lab')
    p.add_argument('--task',choices=[t['id'] for t in tasks.TASKS],default='clamp')
    p.add_argument('--timeout',type=int,default=600); p.add_argument('--context',type=int,default=4096)
    p.add_argument('--workspace'); p.add_argument('--prompt-file'); p.add_argument('--test-command')
    p.add_argument('--read-only',action='store_true'); p.add_argument('--compact',action='store_true'); args=p.parse_args()
    root=ROOT/args.out; root.mkdir(parents=True,exist_ok=False)
    task=tasks.get(args.task)
    if args.workspace:
        workspace=Path(args.workspace).resolve()
        if not workspace.is_dir() or not args.prompt_file or not args.test_command:
            raise ValueError('An existing workspace requires --prompt-file and --test-command')
    else:
        workspace=root/'workspace'; workspace.mkdir()
        (workspace/'solution.py').write_text(tasks.source(task))
        (workspace/'fixture.txt').write_text('LAB_MARKER_73219\n')
    home=root/'codex-home'; home.mkdir()
    (home/'config.toml').write_text('[windows]\nsandbox = "unelevated"\n')
    catalog=json.loads((STUDIO/'infrastructure/nova-codex-models.json').read_text(encoding='utf-8-sig'))
    model=catalog['models'][0]
    model.update(slug=args.model,display_name=args.model+' lab',context_window=args.context,max_context_window=args.context,
                 base_instructions='You are a concise coding agent on Windows PowerShell. Use provided tools to inspect, edit, and verify only this workspace. Do not request escalation. Use PowerShell syntax. For an existing file, call apply_patch with this exact grammar: *** Begin Patch\n*** Update File: relative/path.py\n@@\n-old line\n+new line\n*** End Patch\nNever use File: headers or Git line numbers in @@. After a rejected patch, correct the tool input and retry. Never print patches in your final answer. A failed command is not a successful result. Finish only after an observed successful test, with one short sentence.')
    catalog['models']=[model]
    if args.compact:
        model['base_instructions']='You are a concise coding agent. Follow the task and use the compact JSON action interface supplied by your adapter. Read before editing and verify before finishing.'
    catalog_path=root/'catalog.json'; catalog_path.write_text(json.dumps(catalog))
    env={k:v for k,v in os.environ.items() if not k.startswith(('CODEX_','NOVA_','OPENAI_'))}
    env['CODEX_HOME']=str(home); env['TERM']='xterm-256color'
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    # Tool-shape adaptation already used by Conductor, running on its own ephemeral port.
    js="const fs=require('fs');const {createProxy}=require(process.argv[1]);const s=createProxy({kind:'ollama',baseUrl:process.argv[2]});s.prependListener('request',(req)=>{const chunks=[];req.on('data',c=>chunks.push(c));req.on('end',()=>{if(chunks.length)fs.appendFileSync(process.argv[3],Buffer.concat(chunks).toString()+'\\n');});});s.listen(0,'127.0.0.1',()=>console.log(s.address().port));"
    test_code='from solution import '+task['id']+'; assert all('+task['id']+'(*a)==b for a,b in '+repr(task['cases'])+')'
    test_command=args.test_command or "py -3.12 -c '"+test_code.replace("'","''")+"'"
    proxy_cmd=['node','-e',js,str(STUDIO/'infrastructure/nova-codex-proxy.js'),args.url,str(root/'requests.jsonl')]
    if args.compact:
        import sys
        proxy_cmd=[sys.executable,str(ROOT/'compact_proxy.py'),'--workspace',str(workspace),'--url',args.url,
                   '--log',str(root/'compact-trace.jsonl'),'--test-command',test_command]
    proxy=subprocess.Popen(proxy_cmd,
                           stdout=subprocess.PIPE,stderr=(root/'proxy-errors.log').open('w'),text=True,env=env,creationflags=flags)
    try:
        port=int(proxy.stdout.readline().strip())
        config={'model_provider':'gemma_lab','model_providers.gemma_lab.name':'Gemma Lab',
                'model_providers.gemma_lab.base_url':f'http://127.0.0.1:{port}/v1',
                'model_providers.gemma_lab.wire_api':'responses','model_providers.gemma_lab.requires_openai_auth':False,
                'model_providers.gemma_lab.request_max_retries':0,'model_providers.gemma_lab.stream_max_retries':0,
                'model_providers.gemma_lab.stream_idle_timeout_ms':600000,
                'model_catalog_json':str(catalog_path),'model_context_window':args.context,
                'model_auto_compact_token_limit':args.context-768,'model_reasoning_effort':'minimal',
                'tool_output_token_limit':500,'features.plugins':False,'features.apps':False,
                'features.multi_agent':False,'features.skill_search':False,'features.remote_plugin':False,
                'features.code_mode.enabled':False,'web_search':'disabled'}
        cmd=[str(CODEX),'-a','never','-s','read-only' if args.read_only else 'workspace-write','-C',str(workspace),'-m',args.model]
        for k,v in config.items(): cmd+=['-c',k+'='+json.dumps(v)]
        prompt='Use a shell tool to read fixture.txt. Reply with exactly its contents.' if args.read_only else (
            'Read solution.py. '+task['prompt']+' '
            'Use apply_patch, then run '+test_command+'. '
            'Finish after the test succeeds. Keep tool output short.')
        if args.prompt_file: prompt=Path(args.prompt_file).read_text(encoding='utf-8-sig')
        elif args.compact and not args.read_only:
            prompt='Read solution.py. '+task['prompt']+' Edit with the write action, run the configured test action, then finish after tests pass.'
        cmd+=['exec','--skip-git-repo-check','--json','-o',str(root/'final.txt'),prompt]
        (root/'invocation.json').write_text(json.dumps({'command':cmd,'private_home':str(home)},indent=2))
        start=time.monotonic()
        with (root/'events.jsonl').open('w',encoding='utf-8') as stdout,(root/'stderr.log').open('w',encoding='utf-8') as stderr:
            child=subprocess.Popen(cmd,cwd=workspace,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,creationflags=flags)
            (root/'codex.pid').write_text(str(child.pid))
            try: code=child.wait(timeout=args.timeout); timeout=False
            except subprocess.TimeoutExpired:
                # Only this owned Codex process tree, never a global image-name kill.
                subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True)
                child.wait(timeout=20); code=child.returncode; timeout=True
        try:
            source=(workspace/'solution.py').read_text()
            graded=None if args.workspace else all(run(source,task['id'],a)==v for a,v in task['cases'])
        except Exception: graded=False
        events=[json.loads(line) for line in (root/'events.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        read_verified=any(e.get('item',{}).get('exit_code')==0 and 'LAB_MARKER_73219' in e.get('item',{}).get('aggregated_output','') for e in events)
        result={'exit_code':code,'timeout':timeout,'seconds':time.monotonic()-start,'independent_code_grade':graded,
                'task_id':None if args.workspace else task['id'],'model':args.model,
                'read_only':args.read_only,'read_verified':read_verified,'adapter':'compact' if args.compact else 'native',
                'final':(root/'final.txt').read_text() if (root/'final.txt').exists() else None}
        (root/'result.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result),flush=True)
    finally:
        proxy.terminate(); proxy.wait(timeout=10)

if __name__=='__main__': main()

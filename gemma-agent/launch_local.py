"""Local compact adapter using the launcher's existing authenticated NOVA URL."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--workspace',required=True)
    p.add_argument('--base-url',choices=('http://127.0.0.1:8788','http://192.168.86.51:8787','https://nova.inversolabs.us'),required=True)
    p.add_argument('--model',default='gemma4-codex:pilot-v1')
    p.add_argument('--context',type=int,choices=(4096,8192),default=8192)
    p.add_argument('--sandbox',choices=('workspace-write','read-only'),default='workspace-write')
    p.add_argument('--prompt-file'); p.add_argument('--test-command',default='')
    p.add_argument('--out'); p.add_argument('--timeout',type=int,default=600)
    args=p.parse_args()
    workspace=Path(args.workspace).resolve()
    if not workspace.is_dir(): raise ValueError('Workspace does not exist')
    if not os.environ.get('NOVA_DESKTOP_API_KEY'): raise RuntimeError('Enter your existing NOVA API key in the launcher.')
    codex=Path(os.environ['APPDATA'])/'npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe'
    if not codex.is_file(): raise RuntimeError('Install the current Windows Codex CLI before launching Gemma.')
    out=Path(args.out) if args.out else Path(os.environ['LOCALAPPDATA'])/'NOVA-Gemma/sessions'/time.strftime('%Y%m%d-%H%M%S')
    out=out.resolve(); out.mkdir(parents=True,exist_ok=False)
    env={k:v for k,v in os.environ.items() if not k.startswith(('CODEX_','NOVA_','OPENAI_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1',TERM='xterm-256color')
    proxy_env={**env,'NOVA_DESKTOP_API_KEY':os.environ['NOVA_DESKTOP_API_KEY']}
    proxy=None; child=None
    try:
        proxy=subprocess.Popen([sys.executable,str(ROOT/'compact_proxy.py'),'--workspace',str(workspace),
            '--url',args.base_url+'/v1','--model',args.model,'--nova-bridge',
            '--log',str(out/'actions.jsonl'),'--test-command',args.test_command],
            stdout=subprocess.PIPE,stderr=(out/'proxy-errors.log').open('w'),text=True,
            env=proxy_env,creationflags=subprocess.CREATE_NO_WINDOW)
        port=int(proxy.stdout.readline().strip())
        home=out/'codex-home'; home.mkdir()
        (home/'config.toml').write_text('[windows]\nsandbox = "unelevated"\n[skills.bundled]\nenabled = false\n')
        env['CODEX_HOME']=str(home)
        catalog=json.loads((ROOT.parent/'nova-codex-models.json').read_text(encoding='utf-8-sig'))
        model=catalog['models'][0]
        model.update(slug='gemma-e2b-pilot',display_name='Gemma E2B trained pilot via NOVA',
            context_window=args.context,max_context_window=args.context,supports_parallel_tool_calls=False,
            base_instructions='You are a concise coding agent on Windows PowerShell. Follow the task using the compact JSON action interface supplied by the adapter. Inspect relevant files before editing. Verify changes and report actual results. Never invent successful tests.')
        catalog_file=out/'catalog.json'; catalog_file.write_text(json.dumps(catalog))
        config={'model_provider':'gemma_remote','model_providers.gemma_remote.name':'NOVA Gemma',
            'model_providers.gemma_remote.base_url':f'http://127.0.0.1:{port}/v1',
            'model_providers.gemma_remote.wire_api':'responses','model_providers.gemma_remote.requires_openai_auth':False,
            'model_providers.gemma_remote.request_max_retries':0,'model_providers.gemma_remote.stream_max_retries':0,
            'model_catalog_json':str(catalog_file),'model_context_window':args.context,
            'model_auto_compact_token_limit':args.context-1024,'model_reasoning_effort':'minimal',
            'model_reasoning_summary':'detailed','hide_agent_reasoning':False,
            'tool_output_token_limit':1000,'features.plugins':False,'features.apps':False,
            'features.multi_agent':False,'features.remote_plugin':False,'features.skill_search':False,
            'features.code_mode.enabled':False,'web_search':'disabled'}
        cmd=[str(codex),'-s',args.sandbox,'-C',str(workspace),'-m','gemma-e2b-pilot']
        for k,v in config.items(): cmd+=['-c',k+'='+json.dumps(v)]
        if args.prompt_file:
            cmd+=['exec','--skip-git-repo-check','--json','-o',str(out/'final.txt'),Path(args.prompt_file).read_text(encoding='utf-8-sig')]
            cmd[1:1]=['-c','approval_policy="never"']; stdout=(out/'events.jsonl').open('w',encoding='utf-8')
        else:
            cmd[1:1]=['-a','on-request','--no-alt-screen']; stdout=None
        print('Starting '+args.model+' through your existing NOVA connection. Tools run in '+str(workspace),flush=True)
        print('This is the two-step training pilot, with the improved compact tool adapter.',flush=True)
        child=subprocess.Popen(cmd,cwd=workspace,env=env,stdout=stdout,stderr=(out/'codex-errors.log').open('w',encoding='utf-8'))
        started=time.monotonic()
        while child.poll() is None:
            if proxy.poll() is not None: raise RuntimeError('The compact adapter stopped unexpectedly.')
            if args.prompt_file and time.monotonic()-started>args.timeout: raise TimeoutError('Codex test timed out')
            time.sleep(1)
        if child.returncode: raise RuntimeError('Codex exited with code '+str(child.returncode))
    finally:
        if child and child.poll() is None: subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True)
        if proxy: proxy.terminate(); proxy.wait(timeout=10)
        print('Session logs: '+str(out),flush=True)

if __name__=='__main__': main()

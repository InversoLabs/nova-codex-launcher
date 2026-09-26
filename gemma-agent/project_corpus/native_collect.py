"""Native Codex teacher run through the existing proxy, with NO compact adapter."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from collect import grade,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--out',required=True);p.add_argument('--task',required=True);p.add_argument('--model',default='gpt-oss:20b');p.add_argument('--timeout',type=int,default=600);a=p.parse_args()
    suite=Path(a.suite).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((suite/'manifest.json').read_text(encoding='utf-8'))
    project,task=next((p,t) for p in manifest['projects'] for t in p['tasks'] if t['id']==a.task)
    if project['split']=='test':raise ValueError('Held-out family is not teacher data')
    if not os.environ.get('NOVA_DESKTOP_API_KEY'):raise RuntimeError('Existing NOVA credential required')
    work=out/'workspace';shutil.copytree(suite/'tasks'/a.task,work)
    home=out/'codex-home';home.mkdir()
    (home/'config.toml').write_text('[windows]\nsandbox = "unelevated"\n[skills.bundled]\nenabled = false\n')
    repo=Path(__file__).resolve().parents[2]
    catalog=json.loads((repo/'nova-codex-models.json').read_text(encoding='utf-8-sig'))
    catalog['models']=catalog['models'][:1]
    catalog['models'][0].update(slug=a.model,display_name=a.model+' native teacher',context_window=8192,max_context_window=8192,
        base_instructions='You are a concise coding agent on Windows PowerShell. Use native Codex tools to read the task, edit the project, and run the requested test command. Keep changes inside the workspace. Report only observed results. Do not request escalation. Avoid recursive listings.')
    catalogfile=out/'catalog.json';catalogfile.write_text(json.dumps(catalog))
    codex=Path(os.environ['APPDATA'])/'npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe'
    config={'approval_policy':'never','model_provider':'nova_teacher','model_providers.nova_teacher.name':'NOVA native teacher',
        'model_providers.nova_teacher.base_url':'http://127.0.0.1:8788/v1','model_providers.nova_teacher.wire_api':'responses',
        'model_providers.nova_teacher.env_key':'NOVA_DESKTOP_API_KEY','model_providers.nova_teacher.request_max_retries':0,
        'model_providers.nova_teacher.stream_max_retries':0,'model_catalog_json':str(catalogfile),'model_context_window':8192,
        'model_auto_compact_token_limit':7000,'model_reasoning_effort':'low','tool_output_token_limit':1800,
        'features.plugins':False,'features.apps':False,'features.multi_agent':False,'features.skill_search':False,
        'features.remote_plugin':False,'features.code_mode.enabled':False,'web_search':'disabled'}
    command=[str(codex),'exec','--json','--skip-git-repo-check','-s','workspace-write','-C',str(work),'-m',a.model,'--output-last-message',str(out/'final.txt')]
    for k,v in config.items():command += ['-c',k+'='+json.dumps(v)]
    command+=['-']
    test='& '+' '.join("'"+str(x).replace("'","''")+"'" for x in ['node',Path(__file__).with_name('grade.cjs'),suite/'manifest.json',project['id'],work])
    prompt=task['prompt'].replace('Run the configured browser tests','Use native Codex tools, not compact JSON actions. Run the browser tests')+'\nTest command:\n'+test
    env={k:v for k,v in os.environ.items() if not k.startswith(('CODEX_','OPENAI_'))};env['CODEX_HOME']=str(home)
    record={'task_id':a.task,'family':project['id'],'split':project['split'],'source_model':a.model,'protocol':'native-codex','started':time.time(),'passed':False,'suite_hash':sha(suite/'manifest.json')}
    with (out/'events.jsonl').open('w',encoding='utf-8') as stdout,(out/'stderr.log').open('w',encoding='utf-8') as stderr:
        child=subprocess.Popen(command,cwd=work,env=env,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,text=True,encoding='utf-8')
        try:child.communicate(prompt,timeout=a.timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True);child.wait(timeout=30);record['timeout']=True
    result=grade(suite,project['id'],work,out/'independent-grade.json')
    events=[json.loads(line) for line in (out/'events.jsonl').read_text(encoding='utf-8').splitlines() if line.startswith('{')]
    record.update(exit_code=child.returncode,passed=child.returncode==0 and result['passed'] and any(e.get('type')=='turn.completed' for e in events),finished=time.time())
    (out/'admission.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
if __name__=='__main__':main()

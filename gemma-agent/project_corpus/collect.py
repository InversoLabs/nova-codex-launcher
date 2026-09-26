"""Collect real Codex runs against fresh browser projects; never synthesize results."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def grade(suite,project,workspace,out):
    proc=subprocess.run(['node',str(HERE/'grade.cjs'),str(suite/'manifest.json'),project,str(workspace),str(out)],capture_output=True,text=True,encoding='utf-8',timeout=100)
    return json.loads(out.read_text(encoding='utf-8')) if out.exists() else {'passed':False,'errors':[proc.stderr]}

def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--out',required=True)
    p.add_argument('--model',default='gpt-oss:20b');p.add_argument('--base-url',default='http://127.0.0.1:8788')
    p.add_argument('--limit',type=int,default=1);p.add_argument('--task');p.add_argument('--timeout',type=int,default=600)
    a=p.parse_args();suite=Path(a.suite).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    if not os.environ.get('NOVA_DESKTOP_API_KEY'):raise RuntimeError('Use the existing launcher credential bootstrap')
    manifest=json.loads((suite/'manifest.json').read_text(encoding='utf-8')); results=[]
    for project in manifest['projects']:
        if project['split']=='test':continue  # Never collect training examples on test families.
        for task in project['tasks']:
            if a.task and task['id']!=a.task:continue
            if len(results)>=a.limit:break
            run=out/task['id'];run.mkdir();workspace=run/'workspace'
            source=suite/'tasks'/task['id']
            for name,expected in task['starter_hashes'].items():
                if sha(source/name)!=expected:raise ValueError('Starter hash changed: '+name)
            shutil.copytree(source,workspace)
            prompt=run/'prompt.txt';prompt.write_text(task['prompt'],encoding='utf-8')
            test='& '+ ' '.join("'"+str(x).replace("'","''")+"'" for x in ['node',HERE/'grade.cjs',suite/'manifest.json',project['id'],workspace])
            command=[sys.executable,str(HERE.parent/'launch_local.py'),'--workspace',str(workspace),'--base-url',a.base_url,'--model',a.model,'--context','8192','--prompt-file',str(prompt),'--test-command',test,'--out',str(run/'session'),'--timeout',str(a.timeout)]
            record={'schema':1,'task_id':task['id'],'family':project['id'],'split':project['split'],'source_model':a.model,'kind':'teacher','started':time.time(),'suite_hash':sha(suite/'manifest.json'),'passed':False}
            with (run/'collector.log').open('w',encoding='utf-8') as log:
                proc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=a.timeout+180)
            record['exit_code']=proc.returncode
            # Candidate JS is evaluated only in the browser, with all external requests blocked.
            report=grade(suite,project['id'],workspace,run/'independent-grade.json')
            trace=run/'session/actions.jsonl'
            events=run/'session/events.jsonl'
            steps=[json.loads(line) for line in trace.read_text(encoding='utf-8').splitlines()] if trace.exists() else []
            finished=bool(steps and steps[-1].get('action',{}).get('tool')=='finish' and steps[-1].get('native_item',{}).get('type')=='message')
            record['passed']=proc.returncode==0 and report['passed'] and finished and events.exists()
            record['observed_finish']=finished
            record['final_hashes']={name:sha(workspace/name) for name in ('index.html','app.js','logic.js','style.css') if (workspace/name).is_file()}
            record['evidence_hashes']={str(f.relative_to(run)):sha(f) for f in (trace,events,run/'independent-grade.json') if f.exists()}
            record['finished']=time.time();(run/'admission.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
            results.append(record);(out/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
            print(task['id'],'ACCEPTED' if record['passed'] else 'REJECTED',flush=True)
            # Stop after a failure so a broken transport cannot waste an entire overnight batch.
            if not record['passed']:return
    print(json.dumps({'runs':len(results),'accepted':sum(r['passed'] for r in results)}))
if __name__=='__main__':main()

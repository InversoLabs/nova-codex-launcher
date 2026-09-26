"""Export admitted, observed next actions; no reference solutions or held-out tests."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from collect import grade,sha

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--runs',required=True);p.add_argument('--suite',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    suite=Path(a.suite).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    rows={'train':[],'validation':[]};rejected=[];seen=set()
    manifest=json.loads((suite/'manifest.json').read_text(encoding='utf-8'));projects={p['id']:p for p in manifest['projects']}
    for file in sorted(Path(a.runs).rglob('admission.json')):
        try:
            r=json.loads(file.read_text(encoding='utf-8'));run=file.parent;workspace=run/'workspace'
            project=projects[r['family']]
            if not r['passed'] or r['kind']!='teacher' or project['split']=='test' or r['split']!=project['split']:raise ValueError('Not an admitted training/validation teacher run')
            if r['suite_hash']!=sha(suite/'manifest.json'):raise ValueError('Suite changed')
            for name,h in r['evidence_hashes'].items():
                if sha(run/name)!=h:raise ValueError('Evidence changed')
            for name,h in r['final_hashes'].items():
                if sha(workspace/name)!=h:raise ValueError('Final files changed')
            if not grade(suite,r['family'],workspace,run/'export-recheck.json')['passed']:raise ValueError('Fresh browser grade failed')
            staged=[]
            for line in (run/'session/actions.jsonl').read_text(encoding='utf-8').splitlines():
                step=json.loads(line)
                if step.get('retries',0) or step.get('action')!=step.get('requested_action'):continue
                action=step['action']
                if action.get('tool') not in ('read','write','edit','exec','check','test','finish'):continue
                messages=step['messages']+[{'role':'assistant','content':json.dumps(action,ensure_ascii=False)}]
                value={'messages':messages,'task_id':r['task_id'],'family':r['family'],'split':r['split'],'source_model':r['source_model'],'kind':'teacher','protocol':'compact-native-browser-v1'}
                text=json.dumps(value)
                if re.search(r'-----BEGIN .*PRIVATE KEY|sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]{16,}',text):raise ValueError('Possible credential')
                key=digest(value)
                if key not in seen:staged.append((key,value))
            for key,value in staged:seen.add(key);rows[r['split']].append(value)
        except Exception as exc:rejected.append({'run':str(file),'reason':str(exc)})
    for split,data in rows.items():(out/(split+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data),encoding='utf-8')
    report={'schema':1,'counts':{s:len(v) for s,v in rows.items()},'files':{s:digest(v) for s,v in rows.items()},'rejected':rejected,'reference_allowed':False,'protocol':'compact-native-browser-v1','note':'Observed Codex runs with independent browser recheck. No exact action replay; do not mix blindly with micro-task protocol. Tokenization and training preflight still required.'}
    (out/'manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()

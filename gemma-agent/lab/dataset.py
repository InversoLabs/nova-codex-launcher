"""Replay original lab runs, reject errors and held-out families, export next actions."""
import json
import re
import tempfile
from pathlib import Path
from .core import Workspace, action, digest, initial, PROTOCOL, PROTOCOLS
from .tasks import get

def validated(record,allow_recovery=False):
    task=get(record['task_id'])
    if record.get('schema')!=1 or record.get('task_hash')!=digest(task) or record.get('protocol_hash') not in PROTOCOLS:
        raise ValueError('Schema/task/protocol mismatch')
    if record.get('split')!=task['split'] or record.get('family')!=task['id']:
        raise ValueError('Split/family mismatch')
    if not record.get('success') or not record.get('steps') or record.get('error'):
        raise ValueError('Not a successful run')
    text=json.dumps(record)
    if re.search(r'-----BEGIN .*PRIVATE KEY|sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}',text):
        raise ValueError('Possible credential in record')
    messages=initial(task); messages[0]['content']=PROTOCOLS[record['protocol_hash']]
    examples=[]; finished=False
    with tempfile.TemporaryDirectory() as tmp:
        ws=Workspace(task,Path(tmp)/'workspace')
        for step in record['steps']:
            if finished: raise ValueError('Actions after finish')
            failed=False
            try:
                a=action(step['raw']); result=ws.apply(a)
            except Exception as exc:
                if not allow_recovery: raise ValueError('Protocol error excluded') from exc
                failed=True; result={'error':str(exc)}
            if not failed and a!=step.get('action'): raise ValueError('Raw/action mismatch')
            if result!=step['result']: raise ValueError('Replay mismatch')
            if not failed: examples.append({'messages':messages+[{'role':'assistant','content':step['raw']}],
                             'task_id':task['id'],'family':task['id'],'split':task['split'],
                             'source_model':record['model'],'kind':record['kind']})
            messages=messages+[{'role':'assistant','content':step['raw']},
                               {'role':'user','content':'TOOL_RESULT '+json.dumps(result)}]
            finished=result.get('finished',False)
        if not finished or not ws.grade()['passed'] or ws.file.read_text(encoding='utf-8')!=record['final_source']:
            raise ValueError('Final evidence mismatch')
    return task,examples

def build(inputs,out,allow_reference=False,allow_recovery=False):
    out=Path(out); out.mkdir(parents=True,exist_ok=False)
    rows={'train':[],'validation':[]}; rejected=[]; seen=set(); protocols=set()
    for path in sorted(Path(inputs).rglob('trajectory.json')):
        try:
            record=json.loads(path.read_text(encoding='utf-8'))
            task,examples=validated(record,allow_recovery)
            if task['split']=='test': raise ValueError('Held-out test family excluded')
            if record['kind']=='reference' and not allow_reference: raise ValueError('Reference fixture excluded')
            key=digest([task['id'],[s['raw'] for s in record['steps']]])
            if key in seen: raise ValueError('Duplicate trajectory')
            seen.add(key); rows[task['split']].extend(examples); protocols.add(record['protocol_hash'])
        except Exception as exc: rejected.append({'file':str(path),'reason':str(exc)})
    for split,data in rows.items():
        (out/(split+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in data),encoding='utf-8')
    manifest={'schema':1,'counts':{k:len(v) for k,v in rows.items()},'rejected':rejected,
              'protocol_hashes':sorted(protocols),'files':{s:digest(v) for s,v in rows.items()},
              'reference_allowed':allow_reference,'recovery_allowed':allow_recovery,
              'note':'Micro-task proof of pipeline; not a production training corpus. Failed actions are never supervised targets.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest

import argparse
import json
from pathlib import Path
from .core import Client, execute
from .tasks import TASKS,source
from .dataset import build

class Reference:
    model='deterministic-reference-NOT-a-teacher-model'
    def __init__(self,task):
        self.actions=iter([{'tool':'read','path':'solution.py'},
                           {'tool':'write','path':'solution.py','content':source(task,True)},
                           {'tool':'test'},{'tool':'finish','summary':'Fixed and verified.'}])
    def complete(self,messages): return json.dumps(next(self.actions)),{},0.0

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='command',required=True)
    e=sub.add_parser('evaluate'); e.add_argument('--url',default='http://127.0.0.1:18190/v1')
    e.add_argument('--model',required=True); e.add_argument('--out',required=True)
    e.add_argument('--split',choices=['all','train','validation','test'],default='all')
    e.add_argument('--steps',type=int,default=8); e.add_argument('--timeout',type=int,default=120)
    e.add_argument('--max-tokens',type=int,default=384); e.add_argument('--reasoning-effort',choices=['low','medium','high'])
    e.add_argument('--task'); e.add_argument('--kind',choices=['model','teacher'],default='model')
    r=sub.add_parser('reference'); r.add_argument('--out',required=True)
    d=sub.add_parser('dataset'); d.add_argument('--inputs',required=True); d.add_argument('--out',required=True)
    d.add_argument('--allow-reference',action='store_true')
    d.add_argument('--allow-recovery',action='store_true')
    args=p.parse_args()
    if args.command=='dataset': print(json.dumps(build(args.inputs,args.out,args.allow_reference,args.allow_recovery),indent=2)); return
    out=Path(args.out); out.mkdir(parents=True,exist_ok=False); records=[]
    for task in TASKS:
        if args.command=='evaluate' and ((args.split!='all' and args.split!=task['split']) or (args.task and args.task!=task['id'])): continue
        client=Reference(task) if args.command=='reference' else Client(args.url,args.model,args.timeout,args.max_tokens,args.reasoning_effort)
        rec=execute(task,client,out/task['id'],max_steps=4 if args.command=='reference' else args.steps,
                    kind='reference' if args.command=='reference' else args.kind)
        records.append(rec)
        print(json.dumps({'task':task['id'],'success':rec['success'],'seconds':round(rec['seconds'],2)}),flush=True)
    if not records: raise ValueError('No matching tasks')
    summary={'model':records[0]['model'],'tasks':len(records),'successes':sum(r['success'] for r in records),
             'pass_rate':sum(r['success'] for r in records)/len(records),
             'action_errors':sum('error' in s['result'] for r in records for s in r['steps']),
             'seconds':sum(r['seconds'] for r in records),'scope':'Original pure-Python micro-task baseline, not general repo coding.',
             'protocol_hash':records[0]['protocol_hash']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8'); print(json.dumps(summary),flush=True)

if __name__=='__main__': main()

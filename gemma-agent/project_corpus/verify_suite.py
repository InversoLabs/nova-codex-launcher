"""Verify references pass and each deliberately broken starter fails in a browser."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',required=True);p.add_argument('--out',required=True);p.add_argument('--starters',action='store_true');a=p.parse_args()
    suite=Path(a.suite).resolve(); out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((suite/'manifest.json').read_text(encoding='utf-8'))
    result={'projects':[],'passed':True,'started':time.time()}
    for project in manifest['projects']:
        targets=[('reference',suite/'references'/project['id'],True)]
        if a.starters:targets += [(t['variant'],suite/'tasks'/t['id'],False) for t in project['tasks']]
        for kind,workspace,expected in targets:
            report=out/(project['id']+'--'+kind+'.json')
            r=subprocess.run(['node',str(Path(__file__).with_name('grade.cjs')),str(suite/'manifest.json'),project['id'],str(workspace),str(report)],capture_output=True,text=True,encoding='utf-8',timeout=100)
            evidence=json.loads(report.read_text(encoding='utf-8')) if report.exists() else {'passed':False,'errors':[r.stderr]}
            # A failed starter must fail behavior, not merely lack a browser/runtime.
            valid=(evidence['passed']==expected and (expected or any(e.startswith('case ') for e in evidence['errors'])))
            result['projects'].append({'project':project['id'],'variant':kind,'expected_pass':expected,'valid':valid,'report':str(report)})
            result['passed'] &= valid
            print(project['id'],kind,'OK' if valid else 'FAIL',flush=True)
            (out/'summary.json').write_text(json.dumps(result,indent=2))
    if not result['passed']:raise SystemExit(1)
if __name__=='__main__':main()

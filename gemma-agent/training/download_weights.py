"""Resumable, bounded parallel public-weight download with full SHA-256 verification."""
import concurrent.futures
import argparse
import hashlib
import json
import subprocess
import shutil
import time
import urllib.request
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--assemble-only',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/'training/gemma-e2b.json').read_text())
    folder=root/'models'/cfg['revision']; folder.mkdir(parents=True,exist_ok=True)
    api='https://huggingface.co/api/models/'+cfg['base_model']+'/revision/'+cfg['revision']+'?blobs=true'
    with urllib.request.urlopen(api,timeout=30) as response: metadata=json.load(response)
    if metadata['sha']!=cfg['revision']: raise ValueError('Revision mismatch')
    spec=next(f for f in metadata['siblings'] if f['rfilename']=='model.safetensors')
    size=spec['size']; expected=spec['lfs']['sha256']
    url='https://huggingface.co/'+cfg['base_model']+'/resolve/'+cfg['revision']+'/model.safetensors?download=true'
    parts=folder/'download-parts'; parts.mkdir(exist_ok=True)
    curl=shutil.which('curl.exe') or shutil.which('curl')
    if not curl: raise RuntimeError('curl is required')
    chunk=64*1024**2; count=(size+chunk-1)//chunk; started=time.monotonic()
    def fetch(index):
        start=index*chunk; end=min(size,start+chunk)-1
        target=parts/('%04d.part'%index)
        if target.exists() and target.stat().st_size==end-start+1: return target
        for attempt in range(3):
            result=subprocess.run([curl,'--fail','--location','--silent','--show-error',
                '--connect-timeout','20','--max-time','180','--range',f'{start}-{end}',
                '--output',str(target),url],capture_output=True,timeout=190,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode==0 and target.stat().st_size==end-start+1: return target
        raise RuntimeError('Weight chunk failed: '+str(index))
    completed=0
    if not args.assemble_only:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for future in concurrent.futures.as_completed([pool.submit(fetch,i) for i in range(count)]):
                part=future.result(); completed+=part.stat().st_size
                progress={'completed_bytes':completed,'total_bytes':size,'seconds':time.monotonic()-started}
                (folder/'download-progress.json').write_text(json.dumps(progress))
                print(json.dumps(progress),flush=True)
    temporary=folder/'model.safetensors.verifying'; digest=hashlib.sha256()
    with temporary.open('wb') as output:
        for index in range(count):
            part=parts/('%04d.part'%index)
            needed=min(chunk,size-index*chunk)
            while not part.exists() or part.stat().st_size!=needed:
                if time.monotonic()-started>1800: raise TimeoutError('Weight assembly waited 30 minutes for missing chunks')
                time.sleep(1)
            with part.open('rb') as source:
                for block in iter(lambda:source.read(8*1024**2),b''):
                    digest.update(block); output.write(block)
            if index%16==0: print(json.dumps({'assembled_chunks':index+1,'total_chunks':count}),flush=True)
    if digest.hexdigest()!=expected: raise ValueError('Full weight SHA-256 mismatch')
    temporary.replace(folder/'model.safetensors')
    (folder/'lab-source.json').write_text(json.dumps({'repo':cfg['base_model'],'revision':cfg['revision']},indent=2))
    (folder/'weight-integrity.json').write_text(json.dumps({'sha256':expected,'bytes':size,'verified':True},indent=2))
    print('BASE_READY '+str(folder),flush=True)

if __name__=='__main__': main()

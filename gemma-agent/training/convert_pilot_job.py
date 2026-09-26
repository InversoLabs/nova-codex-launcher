"""Memory-bounded CPU conversion, leaving existing inference models alone."""
import ctypes
import json
import os
import subprocess
import time
from pathlib import Path
from run_pilot_job import request,ensure_idle

class Memory(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(name,ctypes.c_ulonglong) for name in
        ('total','available','total_page','available_page','total_virtual','available_virtual','extended')]

def available():
    memory=Memory(); memory.length=ctypes.sizeof(memory)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)): raise OSError('Cannot read available RAM')
    return memory.available

def main():
    root=Path(__file__).resolve().parents[1]
    out=root/'runs/convert-pilot-v5'; out.mkdir(exist_ok=False)
    state={'phase':'preflight','success':False,'restored':None}
    def update(**values):
        state.update(values); (out/'result.json').write_text(json.dumps(state,indent=2)); print(json.dumps(state),flush=True)
    deadline=time.monotonic()+900
    while True:
        try: ensure_idle(request('http://127.0.0.1:18183/api/projects')); break
        except RuntimeError:
            if time.monotonic()>deadline: raise RuntimeError('Conductor stayed active; conversion was not started')
            update(phase='waiting_for_conductor'); time.sleep(15)
    env={**os.environ,'OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','PYTHONDONTWRITEBYTECODE':'1'}
    def run(command,name):
        with (out/(name+'.log')).open('w',encoding='utf-8') as log:
            child=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            update(phase=name,pid=child.pid)
            started=time.monotonic()
            try:
                while child.poll() is None:
                    if available()<4*1024**3: raise RuntimeError('Stopped export to preserve at least 4GB free RAM')
                    if time.monotonic()-started>1200: raise TimeoutError(name+' exceeded 20 minutes')
                    time.sleep(2)
                if child.returncode: raise RuntimeError(name+' failed; inspect log')
            finally:
                if child.poll() is None:
                    subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True)
                    child.wait(timeout=30)
    try:
        if available()<8*1024**3: raise RuntimeError('Chunked conversion needs at least 8GB available RAM')
        run([str(root/'.venv-training/Scripts/python.exe'),'-u',str(root/'training/convert_chunked.py'),
            str(root/'runs/export-pilot-v1/export/merged'),'--outfile',str(out/'gemma-pilot-f16.gguf'),
            '--outtype','f16'],'convert')
        run([str(Path.home()/'NOVA-Agent/llama.cpp/llama-quantize.exe'),str(out/'gemma-pilot-f16.gguf'),
            str(out/'gemma-pilot-q4_0.gguf'),'Q4_0','2'],'quantize')
        update(success=True)
    except Exception as exc: update(error=str(exc))
    finally:
        update(phase='complete' if state['success'] else 'failed')

if __name__=='__main__': main()

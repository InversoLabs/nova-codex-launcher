"""Download the pinned public training base into the lab, never the shared cache."""
import os
os.environ['HF_HUB_DISABLE_XET']='1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN']='1'
import json
import argparse
from pathlib import Path
from huggingface_hub import hf_hub_download

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--metadata-only',action='store_true'); args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/'training/gemma-e2b.json').read_text())
    out=root/'models'/cfg['revision']; out.mkdir(parents=True,exist_ok=True)
    for name in ['config.json','tokenizer_config.json','chat_template.jinja','tokenizer.json','generation_config.json','model.safetensors']:
        if args.metadata_only and name=='model.safetensors': continue
        print('DOWNLOADING '+name,flush=True)
        hf_hub_download(cfg['base_model'],name,revision=cfg['revision'],local_dir=out,token=False)
        print('READY '+name,flush=True)
    if not args.metadata_only:
        (out/'lab-source.json').write_text(json.dumps({'repo':cfg['base_model'],'revision':cfg['revision']},indent=2))
    print(('METADATA_READY ' if args.metadata_only else 'BASE_READY ')+str(out),flush=True)

if __name__=='__main__': main()

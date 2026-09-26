"""Merge into a NEW checkpoint, then optionally convert to GGUF. Never overwrite base."""
import argparse
import json
import subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser(); p.add_argument('--base',required=True); p.add_argument('--revision',required=True)
    p.add_argument('--adapter',required=True); p.add_argument('--out',required=True)
    p.add_argument('--llama-cpp'); p.add_argument('--execute',action='store_true')
    args=p.parse_args(); out=Path(args.out).resolve()
    if out.exists(): raise ValueError('Use a new output directory')
    plan={'base':args.base,'revision':args.revision,'adapter':str(Path(args.adapter).resolve()),
          'out':str(out),'quantization':'Q4_0','note':'Re-evaluate merged and quantized artifacts; LoRA does not automatically preserve QAT calibration.'}
    print(json.dumps(plan,indent=2))
    if not args.execute: return
    import torch
    torch.set_num_threads(2)
    from transformers import Gemma4ForCausalLM,Gemma4TextConfig,AutoTokenizer
    from peft import PeftModel
    config=Gemma4TextConfig.from_dict(json.loads((Path(args.base)/'config.json').read_text())['text_config'])
    base,loading=Gemma4ForCausalLM.from_pretrained(args.base,revision=args.revision,config=config,
        key_mapping={r'^model.language_model\.':'model.'},dtype=torch.float16,
        device_map={'':'cpu'},trust_remote_code=False,output_loading_info=True)
    if [k for k in loading.get('missing_keys',[]) if k!='lm_head.weight'] or loading.get('mismatched_keys') or loading.get('error_msgs'):
        raise RuntimeError('Text export weights did not load completely: '+str(loading))
    model=PeftModel.from_pretrained(base,args.adapter).merge_and_unload(safe_merge=True)
    model.save_pretrained(out/'merged',safe_serialization=True)
    AutoTokenizer.from_pretrained(args.base,revision=args.revision,trust_remote_code=False).save_pretrained(out/'merged')
    (out/'export-manifest.json').write_text(json.dumps(plan,indent=2))
    if args.llama_cpp:
        import sys
        llama=Path(args.llama_cpp).resolve()
        subprocess.run([sys.executable,str(llama/'convert_hf_to_gguf.py'),str(out/'merged'),
                        '--outfile',str(out/'gemma-agent-f16.gguf'),'--outtype','f16'],check=True)
        candidates=[llama/'build/bin/llama-quantize',llama/'build/bin/Release/llama-quantize.exe',llama/'llama-quantize.exe']
        quantizer=next((x for x in candidates if x.exists()),None)
        if quantizer is None: raise FileNotFoundError('llama-quantize not found')
        subprocess.run([str(quantizer),str(out/'gemma-agent-f16.gguf'),str(out/'gemma-agent-q4_0.gguf'),'Q4_0'],check=True)

if __name__=='__main__': main()

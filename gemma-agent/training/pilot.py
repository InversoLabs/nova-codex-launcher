"""Bounded experimental E2B QLoRA pilot: frozen PLE embeddings stay in RAM.

This tests real pretrained weight updates, not production training quality.
Only verified datasets and a complete local pinned base are accepted.
"""
import argparse
import json
import time
from pathlib import Path
from train import check_data,tokenize_example
from placement import text_device_map

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base',required=True); p.add_argument('--data',required=True)
    p.add_argument('--out',required=True); p.add_argument('--execute',action='store_true')
    p.add_argument('--steps',type=int,default=2); p.add_argument('--device',type=int,default=1)
    args=p.parse_args()
    if not 1<=args.steps<=10: raise ValueError('Pilot is limited to 1-10 steps')
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/'training/gemma-e2b.json').read_text())
    base=Path(args.base).resolve(); out=Path(args.out).resolve()
    source=json.loads((base/'lab-source.json').read_text())
    if source!={'repo':cfg['base_model'],'revision':cfg['revision']}: raise ValueError('Base source mismatch')
    integrity=json.loads((base/'weight-integrity.json').read_text())
    if not integrity.get('verified') or integrity['bytes']!=(base/'model.safetensors').stat().st_size:
        raise ValueError('Verified complete weights are required')
    train,valid=check_data(args.data,cfg,smoke=True)
    if any(row.get('kind')=='reference' for row in train+valid): raise ValueError('No reference fixtures in real-weight pilot')
    if not args.execute:
        print(json.dumps({'pilot_ready':True,'steps':args.steps,'train_examples':len(train),'validation_examples':len(valid)})); return
    out.mkdir(parents=True,exist_ok=False)
    report={'scope':'Real-weight pilot only; too little data to claim improved coding capability.',
            'source':source,'steps':[],'success':False}
    try:
        import torch
        import psutil
        from transformers import AutoTokenizer,Gemma4TextConfig,Gemma4ForCausalLM,BitsAndBytesConfig
        from peft import LoraConfig,get_peft_model
        from accelerate.hooks import remove_hook_from_module
        torch.set_num_threads(2); torch.manual_seed(42); torch.cuda.set_device(args.device)
        free,total=torch.cuda.mem_get_info()
        if free<3*1024**3: raise RuntimeError('Pilot needs at least 3 GiB free on the selected GPU')
        if psutil.virtual_memory().available<12*1024**3:
            raise RuntimeError('Pilot needs at least 12 GiB available system RAM')
        device='cuda:'+str(args.device)
        # Pascal consumer/workstation cards have slow native half arithmetic.
        compute=torch.float32 if torch.cuda.get_device_capability()[0]<7 else torch.float16
        report['quantized_compute_dtype']=str(compute)
        tokenizer=AutoTokenizer.from_pretrained(base,local_files_only=True)
        text_cfg=Gemma4TextConfig.from_dict(json.loads((base/'config.json').read_text())['text_config'])
        print('LOADING_TEXT_MODEL',flush=True)
        model,info=Gemma4ForCausalLM.from_pretrained(base,config=text_cfg,local_files_only=True,
            key_mapping={r'^model.language_model\.':'model.'},dtype=torch.float16,
            quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',
                bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=compute,
                llm_int8_enable_fp32_cpu_offload=True),
            device_map=text_device_map(text_cfg,device),
            attn_implementation='eager',output_loading_info=True)
        missing=[k for k in info.get('missing_keys',[]) if k!='lm_head.weight']
        if missing or info.get('mismatched_keys') or info.get('error_msgs'):
            raise RuntimeError('Training base did not load completely: '+str(info))
        # Accelerate otherwise moves the entire CPU embedding table to the GPU
        # during forward. Keep it resident on CPU and transfer only looked-up rows.
        embedding=model.model.embed_tokens_per_layer
        remove_hook_from_module(embedding,recurse=True)
        if any(t.device.type=='meta' for t in embedding.parameters()): raise RuntimeError('PLE embedding was not materialized')
        embedding.to(device='cpu',dtype=torch.float16)
        original=embedding.forward
        def cpu_embedding(ids):
            return original(ids.to('cpu')).to(ids.device)
        embedding.forward=cpu_embedding
        for parameter in model.parameters(): parameter.requires_grad_(False)
        model.config.use_cache=False
        model=get_peft_model(model,LoraConfig(r=4,lora_alpha=8,lora_dropout=0.0,
            target_modules=['q_proj','v_proj','o_proj'],task_type='CAUSAL_LM',bias='none'))
        model.enable_input_require_grads()
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        trainable=[v for v in model.parameters() if v.requires_grad]
        optimizer=torch.optim.AdamW(trainable,lr=5e-5)
        encoded=[tokenize_example(tokenizer,row,1024) for row in train]
        encoded=[r for r in encoded if r is not None]
        if not encoded: raise ValueError('No complete training actions fit the pilot context')
        report['retained_examples']=len(encoded)
        report['trainable_parameters']=sum(p.numel() for p in trainable)
        validation=next((r for row in valid if (r:=tokenize_example(tokenizer,row,1024)) is not None),None)
        if validation is None: raise ValueError('No complete validation action fits')
        def validation_loss():
            model.eval()
            with torch.no_grad():
                vi=torch.tensor([validation['input_ids']],device=device)
                vl=torch.tensor([validation['labels']],device=device)
                vp=(vl[0,1:]!=-100).nonzero().flatten()
                output=model(input_ids=vi,use_cache=False,logits_to_keep=vp).logits
                loss=torch.nn.functional.cross_entropy(output[0].float(),vl[0,vp+1])
            return float(loss)
        report['initial_validation_loss']=validation_loss()
        print(json.dumps({'initial_validation_loss':report['initial_validation_loss']}),flush=True)
        model.train()
        for step in range(args.steps):
            started=time.monotonic(); row=encoded[step%len(encoded)]
            ids=torch.tensor([row['input_ids']],device=device)
            labels=torch.tensor([row['labels']],device=device)
            positions=(labels[0,1:]!=-100).nonzero().flatten()
            if not len(positions): raise ValueError('Empty supervised action')
            # Compute vocabulary logits only where a supervised action is predicted.
            logits=model(input_ids=ids,use_cache=False,logits_to_keep=positions).logits
            loss=torch.nn.functional.cross_entropy(logits[0].float(),labels[0,positions+1])
            if not torch.isfinite(loss): raise RuntimeError('Non-finite loss')
            loss.backward()
            norm=torch.nn.utils.clip_grad_norm_(trainable,1.0)
            if not torch.isfinite(norm) or norm<=0: raise RuntimeError('Invalid or zero adapter gradients')
            optimizer.step(); optimizer.zero_grad(set_to_none=True)
            result={'step':step+1,'loss':float(loss.detach()),'gradient_norm':float(norm),
                    'seconds':time.monotonic()-started,'peak_gpu_bytes':torch.cuda.max_memory_allocated()}
            report['steps'].append(result); print(json.dumps(result),flush=True)
            (out/'pilot-report.json').write_text(json.dumps(report,indent=2))
            del logits,loss,ids,labels
        model.save_pretrained(out/'adapter'); tokenizer.save_pretrained(out/'adapter')
        report['final_validation_loss']=validation_loss()
        report['success']=True
    except Exception as exc:
        report['error']=type(exc).__name__+': '+str(exc)
        raise
    finally:
        (out/'pilot-report.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__': main()

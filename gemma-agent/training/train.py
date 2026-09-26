"""Assistant-target-only Gemma LoRA/QLoRA with a fail-closed preflight.

Default invocation only validates data/config. --execute loads weights and trains.
Only accepted lab-generated datasets should be passed to this entry point.
"""
import argparse
import hashlib
import importlib.metadata
import json
import re
from pathlib import Path

def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]

def check_data(folder,config,smoke=False):
    folder=Path(folder); manifest=json.loads((folder/'manifest.json').read_text())
    if manifest.get('reference_allowed') and not smoke: raise ValueError('Reference fixtures are not teacher data')
    train,valid=read_rows(folder/'train.jsonl'),read_rows(folder/'validation.jsonl')
    for split,rows in [('train',train),('validation',valid)]:
        calculated=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
        if calculated!=manifest['files'][split]: raise ValueError('Dataset hash mismatch')
        if any(r['split']!=split or r['messages'][-1]['role']!='assistant' for r in rows): raise ValueError('Invalid split/target')
        if not rows: raise ValueError('Both training and validation need examples')
        if not smoke and (len(rows)<config['min_'+split+'_examples'] or len({r['family'] for r in rows})<config['min_'+split+'_families']):
            raise ValueError('Insufficient independent examples/families in '+split)
    if {r['family'] for r in train}&{r['family'] for r in valid}: raise ValueError('Family leakage')
    return train,valid

def tokenize_example(tokenizer,row,max_length):
    messages=row['messages']
    prefix=tokenizer.apply_chat_template(messages[:-1],tokenize=True,add_generation_prompt=True,enable_thinking=False,return_dict=False)
    full=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=False,enable_thinking=False,return_dict=False)
    if full[:len(prefix)]!=prefix: raise ValueError('Template prefix mismatch; refusing ambiguous assistant mask')
    if len(full)>max_length: return None  # Never truncate away the supervised action.
    if len(full)<=len(prefix): raise ValueError('Empty assistant target')
    return {'input_ids':full,'attention_mask':[1]*len(full),'labels':[-100]*len(prefix)+full[len(prefix):]}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--config',default='training/gemma-e2b.json')
    p.add_argument('--data',required=True); p.add_argument('--out',required=True)
    p.add_argument('--execute',action='store_true'); p.add_argument('--smoke',action='store_true')
    p.add_argument('--method',choices=['lora','qlora']); p.add_argument('--device',default='cuda:0')
    args=p.parse_args(); cfg=json.loads(Path(args.config).read_text())
    if args.method: cfg['method']=args.method
    train,valid=check_data(args.data,cfg,args.smoke)
    report={'data_valid':True,'train_examples':len(train),'validation_examples':len(valid),'config':cfg,
            'execution_requested':args.execute,'smoke':args.smoke}
    out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    (out/'preflight.json').write_text(json.dumps(report,indent=2))
    if not args.execute:
        print(json.dumps(report,indent=2)); return
    if not re.fullmatch(r'[0-9a-f]{40}',cfg.get('revision') or ''):
        raise ValueError('Pin a verified 40-character Hugging Face commit revision before training')
    import torch
    from transformers import AutoTokenizer, Gemma4ForCausalLM, Gemma4TextConfig, BitsAndBytesConfig, Trainer, TrainingArguments
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    if not torch.cuda.is_available() or not args.device.startswith('cuda:'):
        raise RuntimeError('This server training recipe requires a compatible, available CUDA GPU')
    index=int(args.device.split(':')[1]); torch.cuda.set_device(index)
    free,total=torch.cuda.mem_get_info(index)
    # Embeddings remain higher precision; the E2B name is not a 2B total-weights budget.
    if free < 6*1024**3: raise RuntimeError('Need at least 6 GiB free on one device for this conservative recipe. No production models were unloaded.')
    torch.manual_seed(cfg['seed'])
    tokenizer=AutoTokenizer.from_pretrained(cfg['base_model'],revision=cfg['revision'],trust_remote_code=False)
    if tokenizer.pad_token_id is None: tokenizer.pad_token=tokenizer.eos_token
    encoded=[]
    for split in (train,valid):
        rows=[tokenize_example(tokenizer,r,cfg['max_length']) for r in split]
        kept=[r for r in rows if r is not None]
        if not kept: raise ValueError('No full examples fit context')
        encoded.append(kept)
    compute=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    kwargs={'revision':cfg['revision'],'trust_remote_code':False,'dtype':compute,
            'device_map':{'':index},'attn_implementation':'eager'}
    if cfg['method']=='qlora':
        kwargs['quantization_config']=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',
            bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=compute)
    text_config=Gemma4TextConfig.from_pretrained(cfg['base_model'],revision=cfg['revision'])
    model,loading=Gemma4ForCausalLM.from_pretrained(cfg['base_model'],config=text_config,
        key_mapping={r'^model.language_model\.':'model.'},output_loading_info=True,**kwargs)
    if [k for k in loading.get('missing_keys',[]) if k!='lm_head.weight'] or loading.get('mismatched_keys') or loading.get('error_msgs'):
        raise RuntimeError('Text training weights did not load completely: '+str(loading))
    if cfg['method']=='qlora': model=prepare_model_for_kbit_training(model)
    model.config.use_cache=False
    # Exclude vision/audio modules even if upstream auto-class changes.
    targets=[name for name,_ in model.named_modules() if name.split('.')[-1] in cfg['target_modules']
             and not any(x in name for x in ('vision','audio','embed'))]
    if not targets: raise ValueError('No text LoRA targets matched')
    model=get_peft_model(model,LoraConfig(r=cfg['rank'],lora_alpha=cfg['alpha'],lora_dropout=cfg['dropout'],
        target_modules=targets,task_type='CAUSAL_LM',bias='none'))
    model.enable_input_require_grads()
    def collate(rows):
        n=max(len(r['input_ids']) for r in rows)
        pads={'input_ids':tokenizer.pad_token_id,'attention_mask':0,'labels':-100}
        return {k:torch.tensor([r[k]+[pad]*(n-len(r[k])) for r in rows]) for k,pad in pads.items()}
    steps=2 if args.smoke else cfg['max_steps']
    training_args=TrainingArguments(output_dir=str(out/'checkpoints'),per_device_train_batch_size=1,
        per_device_eval_batch_size=1,gradient_accumulation_steps=cfg['gradient_accumulation_steps'],
        learning_rate=cfg['learning_rate'],max_steps=steps,gradient_checkpointing=True,
        gradient_checkpointing_kwargs={'use_reentrant':False},fp16=compute==torch.float16,bf16=compute==torch.bfloat16,
        optim='adamw_torch',logging_steps=1,save_steps=max(1,steps//2),save_total_limit=2,
        eval_strategy='steps',eval_steps=max(1,steps//2),report_to=[],seed=cfg['seed'],dataloader_num_workers=0)
    trainer=Trainer(model=model,args=training_args,train_dataset=encoded[0],eval_dataset=encoded[1],data_collator=collate)
    trainer.train(); model.save_pretrained(out/'adapter'); tokenizer.save_pretrained(out/'adapter')
    metrics=trainer.evaluate()
    report.update(metrics=metrics,retained_examples=[len(x) for x in encoded],
                  peak_gpu_bytes=torch.cuda.max_memory_allocated(index),
                  versions={n:importlib.metadata.version(n) for n in ['torch','transformers','peft','bitsandbytes']})
    (out/'training-report.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__': main()

"""Tiny synthetic architecture/backend check; does not train the real Gemma model."""
import importlib.metadata
import argparse
import json
import tempfile
from pathlib import Path
from placement import text_device_map

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--allow-backend-probe',action='store_true')
    args=parser.parse_args()
    if not args.allow_backend_probe:
        raise SystemExit('Backend probe disabled by default after an unresponsive server episode. Investigate the runtime in isolation before explicitly enabling it.')
    import torch
    from transformers import Gemma4TextConfig, Gemma4ForCausalLM
    from peft import LoraConfig,get_peft_model
    torch.set_num_threads(2)
    result={'versions':{p:importlib.metadata.version(p) for p in ['torch','transformers','peft','accelerate','bitsandbytes']},
            'cuda_available':torch.cuda.is_available(),'devices':[],
            'scope':'Synthetic tiny Gemma4 architecture and NF4 backend checks only; no pretrained fine-tune.'}
    for i in range(torch.cuda.device_count()):
        result['devices'].append({'name':torch.cuda.get_device_name(i),'capability':torch.cuda.get_device_capability(i),
                                  'free_total_bytes':torch.cuda.mem_get_info(i)})
    try:
        config=Gemma4TextConfig(vocab_size=256,hidden_size=64,intermediate_size=128,num_hidden_layers=4,
            num_attention_heads=4,num_key_value_heads=2,head_dim=16,global_head_dim=16,
            hidden_size_per_layer_input=16,vocab_size_per_layer_input=256,num_kv_shared_layers=2,sliding_window=32,
            layer_types=['sliding_attention','full_attention']*2,max_position_embeddings=128)
        model=Gemma4ForCausalLM(config)
        if sum(p.numel() for p in model.parameters())>1_000_000:
            raise RuntimeError('Synthetic probe unexpectedly exceeds one million parameters')
        ids=torch.randint(0,256,(1,16))
        model.eval()
        with torch.no_grad():
            cached=model(input_ids=ids,use_cache=True).logits
            uncached=model(input_ids=ids,use_cache=False).logits
        difference=float((cached-uncached).abs().max())
        result['kv_shared_training_parity']={'max_logit_difference':difference,'passed':difference<1e-5}
        if difference>=1e-5: raise RuntimeError('KV-shared cache/no-cache parity failed')
        model=get_peft_model(model,LoraConfig(r=2,lora_alpha=4,target_modules=['q_proj','v_proj','o_proj'],task_type='CAUSAL_LM'))
        model.train()
        optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=1e-3)
        output=model(input_ids=ids,labels=ids,use_cache=False); output.loss.backward()
        nonzero=sum(p.grad is not None and bool(p.grad.abs().sum()>0) for p in model.parameters() if p.requires_grad)
        optimizer.step()
        result['tiny_gemma_lora']={'loss':float(output.loss.detach()),'nonzero_gradient_tensors':nonzero,'passed':nonzero>0}
    except Exception as exc: result['tiny_gemma_lora']={'error':str(exc),'passed':False}
    try:
        if not torch.cuda.is_available(): raise RuntimeError('No CUDA device')
        import bitsandbytes as bnb
        # Use the first GPU; current inference benchmark uses the second.
        layer=bnb.nn.Linear4bit(64,64,bias=False,compute_dtype=torch.float16,quant_type='nf4').to('cuda:0')
        x=torch.randn(1,64,device='cuda:0',dtype=torch.float16,requires_grad=True)
        y=layer(x); y.float().sum().backward()
        result['nf4']={'passed':bool(torch.isfinite(y).all() and torch.isfinite(x.grad).all())}
    except Exception as exc: result['nf4']={'passed':False,'error':str(exc)}
    try:
        from transformers import BitsAndBytesConfig
        from accelerate.hooks import remove_hook_from_module
        from safetensors.torch import load_file,save_file
        with tempfile.TemporaryDirectory() as temporary:
            Gemma4ForCausalLM(config).save_pretrained(temporary)
            checkpoint=Path(temporary)/'model.safetensors'
            tensors={k:v.clone() for k,v in load_file(checkpoint).items()}
            # Emulate the public multimodal checkpoint's text tensor namespace.
            save_file({('model.language_model.'+k[len('model.'):] if k.startswith('model.') else k):v
                       for k,v in tensors.items()},checkpoint,metadata={'format':'pt'})
            hybrid,loading=Gemma4ForCausalLM.from_pretrained(temporary,config=config,dtype=torch.float16,
                key_mapping={r'^model.language_model\.':'model.'},output_loading_info=True,
                attn_implementation='eager',
                quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',
                    bnb_4bit_compute_dtype=torch.float32,llm_int8_enable_fp32_cpu_offload=True),
                device_map=text_device_map(config,'cuda:1'))
            if [k for k in loading.get('missing_keys',[]) if k!='lm_head.weight'] or loading.get('mismatched_keys'):
                raise RuntimeError('Text checkpoint mapping failed: '+str(loading))
            embedding=hybrid.model.embed_tokens_per_layer
            remove_hook_from_module(embedding,recurse=True)
            embedding.to(device='cpu',dtype=torch.float16)
            original=embedding.forward
            embedding.forward=lambda ids: original(ids.to('cpu')).to(ids.device)
            for parameter in hybrid.parameters(): parameter.requires_grad_(False)
            hybrid=get_peft_model(hybrid,LoraConfig(r=2,lora_alpha=4,
                target_modules=['q_proj','v_proj','o_proj'],task_type='CAUSAL_LM'))
            hybrid.enable_input_require_grads()
            hybrid.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
            hybrid.train(); cuda_ids=ids.to('cuda:1')
            output=hybrid(input_ids=cuda_ids,labels=cuda_ids,use_cache=False)
            output.loss.backward()
            good=sum(p.grad is not None and bool(torch.isfinite(p.grad).all()) and bool(p.grad.abs().sum()>0)
                     for p in hybrid.parameters() if p.requires_grad)
            result['hybrid_cpu_embeddings']={'passed':good>0,'loss':float(output.loss.detach()),
                'nonzero_gradient_tensors':good,'embedding_device':str(embedding.weight.device)}
    except Exception as exc: result['hybrid_cpu_embeddings']={'passed':False,'error':str(exc)}
    Path('runs/backend-probe.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))

if __name__=='__main__': main()

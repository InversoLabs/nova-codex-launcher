"""Explicit module placement avoids a root hook moving CPU tables to CUDA."""
def text_device_map(config, device):
    from accelerate import init_empty_weights
    from transformers import Gemma4ForCausalLM
    with init_empty_weights():
        skeleton = Gemma4ForCausalLM(config)
    placement = {'model.' + name: device for name, _ in skeleton.model.named_children()}
    placement.update({name: device for name, _ in skeleton.named_children() if name != 'model'})
    placement['model.embed_tokens_per_layer'] = 'cpu'
    # A catch-all root entry makes Accelerate recursively move every tensor
    # before installing the more specific CPU hook, exceeding a 4GB device.
    assert '' not in placement and 'model' not in placement
    return placement

"""Pinned official converter with row-wise export of the unchanged 4.38GiB PLE table."""
import io
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONVERTER=ROOT/'vendor/llama-converter'
sys.path[:0]=[str(CONVERTER),str(CONVERTER/'gguf-py')]
import numpy as np
import gguf
from safetensors import safe_open

def chunked(file,key,shape,rows=256):
    def load(start,end):
        with safe_open(str(file),framework='np') as reader:
            return reader.get_slice(key)[start:end]
    return gguf.LazyChunkedTensor(
        [lambda lo=lo,hi=min(lo+rows,shape[0]):load(lo,hi) for lo in range(0,shape[0],rows)],
        tuple(shape),np.float16)

if '--self-test' in sys.argv:
    from safetensors.numpy import save_file
    with tempfile.TemporaryDirectory() as d:
        file=Path(d)/'test.safetensors'; values=np.arange(160,dtype=np.float16).reshape(10,16)
        save_file({'embedding':values},str(file))
        target=Path(d)/'chunked.bin'
        with target.open('wb') as f: chunked(file,'embedding',values.shape,rows=3).quantize(gguf.GGMLQuantizationType.F16).tofile(f)
        assert target.read_bytes()==values.tobytes()
    print('CHUNKED_EXPORT_PARITY_PASSED'); sys.exit(0)

from conversion.gemma import Gemma4Model
from convert_hf_to_gguf import main
original=Gemma4Model.modify_tensors
def bounded(self,data,name,bid):
    for mapped,tensor in original(self,data,name,bid):
        if name=='model.embed_tokens_per_layer.weight':
            # At the pinned converter revision this embedding is only renamed,
            # never rescaled, transposed, or normalized. Preserve exact row bytes.
            if mapped!='per_layer_token_embd.weight': raise ValueError('Unexpected PLE mapping')
            file=self.dir_model/'model.safetensors'
            with safe_open(str(file),framework='np') as reader:
                source=reader.get_slice(name)
                if source.get_shape()!=list(tensor.shape) or source.get_dtype()!='F16':
                    raise ValueError('Chunked export requires the merged FP16 table unchanged')
            yield mapped,chunked(file,name,tensor.shape)
        else: yield mapped,tensor
Gemma4Model.modify_tensors=bounded
main()

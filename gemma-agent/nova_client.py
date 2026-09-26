"""Authenticated chat transport through the existing NOVA bridge; no new tunnel."""
import json
import os
import time
import urllib.request
ALLOWED=('http://127.0.0.1:8788/v1','http://192.168.86.51:8787/v1','https://nova.inversolabs.us/v1')
ACTION_SCHEMA={'oneOf':[
    {'type':'object','properties':{'tool':{'const':tool},**{name:{'type':'string'} for name in fields}},
     'required':['tool',*fields],'additionalProperties':False}
    for tool,fields in [('read',['path']),('write',['path','content']),('exec',['cmd']),('test',[]),('finish',['summary'])]
]}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ValueError('NOVA redirects are disabled to protect the API credential')

class NovaClient:
    def __init__(self,url,model):
        if url.rstrip('/') not in ALLOWED: raise ValueError('Use an existing NOVA bridge URL')
        self.url=url.rstrip('/')+'/chat/completions'; self.model=model
        self.key=os.environ.get('NOVA_DESKTOP_API_KEY')
        if not self.key: raise ValueError('NOVA_DESKTOP_API_KEY is required')
        self.http=urllib.request.build_opener(NoRedirect())
    def complete(self,messages,on_delta=None):
        payload={'model':self.model,'messages':messages,'temperature':0,'seed':42,'max_tokens':2048,'stream':bool(on_delta),
                 'response_format':{'type':'json_schema','json_schema':{'name':'agent_action','strict':True,'schema':ACTION_SCHEMA}}}
        if on_delta: payload['stream_options']={'include_usage':True}
        req=urllib.request.Request(self.url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+self.key})
        start=time.monotonic()
        self.last_finish_reason=None
        with self.http.open(req,timeout=240) as response:
            if on_delta:
                content=''; usage={}; total=0; finished=False
                for line in response:
                    total+=len(line)
                    if total>4_000_000 or time.monotonic()-start>600: raise ValueError('NOVA response exceeded the stream budget')
                    if not line.startswith(b'data:'): continue
                    data=line[5:].strip()
                    if data==b'[DONE]': finished=True; break
                    chunk=json.loads(data)
                    if chunk.get('error'): raise ValueError('NOVA returned a streaming error')
                    if chunk.get('usage'): usage=chunk['usage']
                    for choice in chunk.get('choices',[]):
                        delta=choice.get('delta',{})
                        thinking=delta.get('reasoning') or delta.get('reasoning_content') or ''
                        if thinking: on_delta('reasoning',thinking)
                        piece=delta.get('content') or ''
                        if piece: content+=piece; on_delta('content',piece)
                        if choice.get('finish_reason'): self.last_finish_reason=choice['finish_reason']
                if not finished: raise ValueError('NOVA stream disconnected before completion; no action was executed')
                result={'usage':usage}
            else:
                result=json.loads(response.read(2_000_000))
                choice=result['choices'][0]
                content=choice['message'].get('content')
                self.last_finish_reason=choice.get('finish_reason')
        if not content: raise ValueError('NOVA returned no final action')
        return content,result.get('usage',{}),time.monotonic()-start

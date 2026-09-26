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
    def complete(self,messages):
        payload={'model':self.model,'messages':messages,'temperature':0,'seed':42,'max_tokens':1024,'stream':False,
                 'response_format':{'type':'json_schema','json_schema':{'name':'agent_action','strict':True,'schema':ACTION_SCHEMA}}}
        req=urllib.request.Request(self.url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+self.key})
        start=time.monotonic()
        with self.http.open(req,timeout=240) as response: result=json.loads(response.read(2_000_000))
        content=result['choices'][0]['message'].get('content')
        if not content: raise ValueError('NOVA returned no final action')
        return content,result.get('usage',{}),time.monotonic()-start

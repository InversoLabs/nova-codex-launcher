import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from compact_proxy import Adapter,LiveEvents,local_title
from nova_client import NovaClient

class StreamingTests(unittest.TestCase):
    def client(self,chunks,done=True):
        with patch.dict(os.environ,{'NOVA_DESKTOP_API_KEY':'test-only'}):
            client=NovaClient('http://127.0.0.1:8788/v1','pilot')
        data=b''.join(b'data: '+json.dumps(c).encode()+b'\n\n' for c in chunks)
        if done: data+=b'data: [DONE]\n\n'
        client.http.open=lambda req,timeout:io.BytesIO(data)
        return client
    def test_reasoning_streams_before_complete_action(self):
        client=self.client([
            {'choices':[{'delta':{'reasoning':'Inspect first.'}}]},
            {'choices':[{'delta':{'content':'{"tool":"finish",'}}]},
            {'choices':[{'delta':{'content':'"summary":"done"}'},'finish_reason':'stop'}]},
            {'choices':[],'usage':{'completion_tokens':20}}])
        deltas=[]
        raw,usage,_=client.complete([],lambda *v:deltas.append(v))
        self.assertEqual(deltas[0],('reasoning','Inspect first.'))
        self.assertEqual(json.loads(raw)['summary'],'done')
        self.assertEqual(usage['completion_tokens'],20)
    def test_disconnected_stream_is_rejected(self):
        client=self.client([{'choices':[{'delta':{'content':'{"tool":'}}]}],done=False)
        with self.assertRaisesRegex(ValueError,'disconnected'): client.complete([],lambda *v:None)
    def test_reasoning_item_and_action_have_distinct_indices(self):
        seen=[]; live=LiveEvents(lambda e,d:seen.append((e,d)),'pilot')
        live.delta('reasoning','Inspect first.')
        item={'type':'message','id':'msg_test','role':'assistant','status':'completed','content':[{'type':'output_text','text':'done','annotations':[]}]}
        live.finish(item,{})
        self.assertEqual(seen[-1][1]['response']['id'],seen[0][1]['response']['id'])
        self.assertEqual(len(seen[-1][1]['response']['output']),2)
        self.assertEqual([d['output_index'] for e,d in seen if e=='response.output_item.added'],[0,1])
    def test_title_bypass_never_diverts_tool_turn(self):
        body={'input':'Generate a concise, single-line task title of at most 36 characters.\nUser prompt: Build a webpage'}
        self.assertIsNotNone(local_title(body))
        body['tools']=[{'name':'exec_command'}]
        self.assertIsNone(local_title(body))
    def test_incomplete_action_retries_without_partial_edit(self):
        with tempfile.TemporaryDirectory() as d:
            adapter=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'log','')
            values=iter(['{"tool":"write","path":"file","content":"partial', '{"tool":"finish","summary":"No edits"}'])
            adapter.client.complete=lambda *args:(next(values),{},0)
            item,_=adapter.complete({'tools':[]})
            self.assertEqual(item['type'],'message')
            self.assertFalse((Path(d)/'file').exists())

import base64
import json
from pathlib import Path
import tempfile
import os
import subprocess
import unittest
from compact_proxy import Adapter,local_title
from workspace_tools import apply_file,digest,read_range,verify,replaced_bytes

class ReliabilityTests(unittest.TestCase):
    def test_new_page_does_not_require_deleted_previous_project(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ('script.js','server.js','style.css'):
                (root/name).write_text('old project')
            (root/'old.html').write_text('<script src="old-missing.js"></script>')
            a=Adapter(d,'http://127.0.0.1:18190/v1',root/'log','')
            a.touched.update(('script.js','server.js','style.css'))
            for name in ('script.js','server.js','style.css'): (root/name).unlink()
            (root/'index.html').write_text('<!doctype html><h1>New page</h1>')
            item=a.translate({'tool':'check'},{'exec_command'})
            payload=json.loads(base64.b64decode(json.loads(item['arguments'])['cmd'].split("'")[-2]))
            self.assertEqual(payload['action']['paths'],['index.html'])
            self.assertTrue(verify(d,payload['action']['paths'])['passed'])
            (root/'index.html').write_text('<script src="needed.js"></script>')
            self.assertFalse(verify(d,['index.html'])['passed'])

    def test_explicit_check_does_not_scan_unchanged_project(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'old.js').write_text('broken(')
            a=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'log','')
            item=a.translate({'tool':'check'},{'exec_command'})
            payload=json.loads(base64.b64decode(json.loads(item['arguments'])['cmd'].split("'")[-2]))
            self.assertEqual(payload['action']['paths'],[])

    @unittest.skipUnless(os.name=='nt','Windows sandbox command integration')
    def test_real_powershell_helper_round_trip_and_finish_gate(self):
        with tempfile.TemporaryDirectory(prefix='gemma helper ') as d:
            p=Path(d)/'math.cjs'; p.write_text('module.exports = (a,b) => a - b;')
            (Path(d)/'test.cjs').write_text("require('node:assert/strict').equal(require('./math.cjs')(2,3),5)")
            a=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'log','node test.cjs')
            def execute(item):
                arguments=json.loads(item['arguments'])
                result=subprocess.run(['powershell.exe','-NoProfile','-Command',arguments['cmd']],cwd=d,capture_output=True,text=True,timeout=30)
                output=f'Process exited with code {result.returncode}\nOutput:\n'+result.stdout+result.stderr
                a.observe({'input':[{'type':'function_call_output','call_id':item['call_id'],'output':output}]})
                self.assertEqual(result.returncode,0,output)
            execute(a.translate({'tool':'edit','path':'math.cjs','old':'a - b','new':'a + b'},{'exec_command'}))
            finish={'tool':'finish','summary':'Repaired'}
            execute(a.translate(finish,{'exec_command'}))
            execute(a.translate(finish,{'exec_command'}))
            self.assertIn('configured test command passed',a.translate(finish,{'exec_command'})['content'][0]['text'])
    def test_multiline_edit_preserves_windows_line_endings(self):
        result=replaced_bytes(b'a\r\nb\r\nc\r\n','a\nb','x\ny')
        self.assertEqual(result,b'x\r\ny\r\nc\r\n')
    def test_title_with_environment_prefix_never_calls_model(self):
        body={'input':[{'role':'developer','content':'Permissions'},
             {'role':'user','content':'<environment_context>Windows</environment_context>'},
             {'role':'user','content':[{'type':'input_text','text':'Generate a concise, single-line task title of at most 36 characters and under five words.\nUser prompt: Build a new chat app'}]}]}
        with tempfile.TemporaryDirectory() as d:
            adapter=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'log','')
            adapter.client.complete=lambda *a: self.fail('Title reached inference')
            item,usage=adapter.complete(body)
            self.assertIn('Build',item['content'][0]['text']); self.assertEqual(usage,{})
            body['tools']=[{'name':'exec_command'}]
            self.assertIsNone(local_title(body))
    def test_edit_changes_only_unique_text_and_rejects_stale_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.py'; p.write_text('x = 1\ny = 2\n')
            action={'tool':'edit','path':'a.py','old':'x = 1','new':'x = 3'}
            old=digest(p); apply_file(d,action,old)
            self.assertEqual(p.read_text(),'x = 3\ny = 2\n')
            with self.assertRaisesRegex(ValueError,'changed'): apply_file(d,action,old)
            with self.assertRaisesRegex(ValueError,'exactly once'):
                apply_file(d,{'tool':'edit','path':'a.py','old':' = ','new':'='},digest(p))
    def test_write_creates_parent_and_rejects_escape(self):
        with tempfile.TemporaryDirectory() as d:
            apply_file(d,{'tool':'write','path':'project/index.html','content':'hello'},None)
            self.assertEqual((Path(d)/'project/index.html').read_text(),'hello')
            with self.assertRaises(ValueError): apply_file(d,{'tool':'write','path':'../outside','content':'bad'},None)
    def test_read_can_reach_beyond_original_160_lines(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'a.txt').write_text('\n'.join(str(i) for i in range(300)))
            result=read_range(d,{'path':'a.txt','start':201,'count':3})
            self.assertIn('201: 200',result); self.assertIn('next start=204',result)
    def test_checks_catch_real_syntax_and_missing_assets(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'a.js').write_text('function broken( {')
            (Path(d)/'index.html').write_text('<script src="missing.js"></script>')
            result=verify(d,['a.js','index.html'])
            self.assertFalse(result['passed']); self.assertEqual(len(result['errors']),2)
            (Path(d)/'a.js').write_text('const n = 1;')
            self.assertTrue(verify(d,['a.js'])['passed'])
    def test_finish_requires_checks_then_configured_tests_and_invalidates_after_change(self):
        with tempfile.TemporaryDirectory() as d:
            a=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'log','node test.cjs')
            a.translate({'tool':'write','path':'x.js','content':'const x=1;'}, {'exec_command'})
            (Path(d)/'x.js').write_text('const x=1;')
            finish={'tool':'finish','summary':'done'}
            check=a.translate(finish,{'exec_command'})
            self.assertEqual(a.calls[check['call_id']]['tool'],'check')
            a.observe({'input':[{'type':'function_call_output','call_id':check['call_id'],'output':'Process exited with code 0\nOutput:\nchecks passed'}]})
            test=a.translate(finish,{'exec_command'})
            self.assertEqual(a.calls[test['call_id']]['tool'],'test')
            a.observe({'input':[{'type':'function_call_output','call_id':test['call_id'],'output':'Process exited with code 0\nOutput:\npassed'}]})
            self.assertEqual(a.translate(finish,{'exec_command'})['type'],'message')
            (Path(d)/'x.js').write_text('const x=2;')
            self.assertEqual(a.translate(finish,{'exec_command'})['type'],'function_call')
    def test_failed_check_and_printed_success_do_not_authorize_finish(self):
        with tempfile.TemporaryDirectory() as d:
            a=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'log','')
            (Path(d)/'bad.js').write_text('broken(')
            check=a.translate({'tool':'finish','summary':'done'},{'exec_command'})
            a.observe({'input':[{'type':'function_call_output','call_id':check['call_id'],'output':'Process exited with code 1\nOutput:\nProcess exited with code 0\npassed'}]})
            with self.assertRaisesRegex(ValueError,'Verification failed'): a.translate({'tool':'finish','summary':'done'},{'exec_command'})
    def test_identical_write_and_repeated_similar_edits_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.txt';p.write_text('a'*1000+'0')
            a=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'log','')
            with self.assertRaisesRegex(ValueError,'No change'): a.translate({'tool':'write','path':'x.txt','content':p.read_text()},{'exec_command'})
            for i in range(1,4):
                a.translate({'tool':'write','path':'x.txt','content':'a'*1000+str(i)},{'exec_command'})
                p.write_text('a'*1000+str(i))
            with self.assertRaisesRegex(ValueError,'Repeated similar'): a.translate({'tool':'write','path':'x.txt','content':'a'*1000+'4'},{'exec_command'})
    def test_long_running_verification_is_polled_not_treated_as_pass(self):
        with tempfile.TemporaryDirectory() as d:
            a=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'log','node test.cjs')
            (Path(d)/'x.js').write_text('const x=1;')
            check=a.translate({'tool':'check'},{'exec_command'})
            a.client.complete=lambda *args: self.fail('Pending check should be polled without inference')
            item,_=a.complete({'tools':[{'name':'write_stdin'}],'input':[{'type':'function_call_output','call_id':check['call_id'],'output':'Process running with session ID 123'}]})
            self.assertEqual(item['name'],'write_stdin'); self.assertIsNone(a.checked)
            a.observe({'input':[{'type':'function_call_output','call_id':item['call_id'],'output':'Process exited with code 0\nOutput:\nchecked'}]})
            self.assertIsNotNone(a.checked)
    def test_failed_functional_test_blocks_success(self):
        with tempfile.TemporaryDirectory() as d:
            a=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'log','node test.cjs')
            (Path(d)/'x.js').write_text('const x=1;')
            check=a.translate({'tool':'check'},{'exec_command'})
            a.observe({'input':[{'type':'function_call_output','call_id':check['call_id'],'output':'Process exited with code 0\n'}]})
            test=a.translate({'tool':'test'},{'exec_command'})
            a.observe({'input':[{'type':'function_call_output','call_id':test['call_id'],'output':'Process exited with code 1\nAssertionError'}]})
            with self.assertRaisesRegex(ValueError,'functional test failed'):a.translate({'tool':'finish','summary':'done'},{'exec_command'})
    def test_repeated_invalid_actions_end_as_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.txt';p.write_text('same')
            a=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'log','')
            a.client.complete=lambda *args:(json.dumps({'tool':'write','path':'x.txt','content':'same'}),{},0)
            item,_=a.complete({'tools':[{'name':'exec_command'}]})
            self.assertIn('Task incomplete',item['content'][0]['text'])
            self.assertEqual(p.read_text(),'same')

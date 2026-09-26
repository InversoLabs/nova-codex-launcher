import copy
import json
import tempfile
import unittest
from pathlib import Path
from lab import safe_python,tasks
from lab.core import action,Workspace,execute,Client,final_action_content,teacher_messages
from lab.__main__ import Reference
from lab.dataset import validated,build

class LabTests(unittest.TestCase):
    def test_teacher_transport_does_not_use_reasoning(self):
        raw='{"tool":"read","path":"solution.py"}'
        call={'function':{'name':'assistant','arguments':raw}}
        self.assertEqual(json.loads(final_action_content({'content':'','tool_calls':[call]})),json.loads(raw))
        native={'function':{'name':'agent_action','arguments':json.dumps({'tool':'read','path':'solution.py','summary':'Inspect file','content':''})}}
        self.assertEqual(json.loads(final_action_content({'tool_calls':[native]})),json.loads(raw))
        self.assertEqual(json.loads(final_action_content({'tool_calls':[{'function':{'name':'test','arguments':'{}'}}]})),{'tool':'test'})
        for message in ({'reasoning':raw},{'tool_calls':[call,call]},
                        {'tool_calls':[{'function':{'name':'shell','arguments':raw}}]}):
            with self.assertRaises(ValueError): final_action_content(message)
        transported=teacher_messages([{'role':'assistant','content':raw},{'role':'user','content':'TOOL_RESULT {"content":"example"}'}])
        self.assertEqual(transported[0]['tool_calls'][0]['id'],transported[1]['tool_call_id'])
        self.assertEqual(transported[1]['role'],'tool')
        self.assertEqual(json.loads(transported[1]['content']),{'content':'example'})
    def test_all_reference_solutions_and_broken_fixtures(self):
        for t in tasks.TASKS:
            for args,want in t['cases']: self.assertEqual(safe_python.run(tasks.source(t,True),t['id'],args),want)
            with tempfile.TemporaryDirectory() as tmp:
                self.assertFalse(Workspace(t,Path(tmp)/'w').grade()['passed'],t['id'])

    def test_no_execution_escape(self):
        for body in ['return __import__("os").getcwd()', 'return x.__class__', 'return open("secret")',
                     'return "x" * 1000000000','return 2 ** 1000000000','while True:\n        pass']:
            with self.assertRaises(Exception): safe_python.run('def f(x):\n    '+body,'f',[1])

    def test_paths_and_schema(self):
        for obj in [{'tool':'read','path':'../secret'},{'tool':'shell','command':'whoami'},
                    {'tool':'test','extra':'x'},{'tool':'write','path':'solution.py','content':1}]:
            with self.assertRaises(ValueError): action(json.dumps(obj))

    def test_finish_requires_fresh_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=tasks.TASKS[0]; w=Workspace(t,Path(tmp)/'w')
            with self.assertRaises(ValueError): w.apply({'tool':'finish','summary':'done'})
            with self.assertRaises(ValueError): w.apply({'tool':'write','path':'solution.py','content':tasks.source(t,True)})
            w.apply({'tool':'read','path':'solution.py'})
            w.apply({'tool':'write','path':'solution.py','content':tasks.source(t,True)})
            self.assertTrue(w.apply({'tool':'test'})['passed'])
            w.apply({'tool':'write','path':'solution.py','content':tasks.source(t)})
            with self.assertRaises(ValueError): w.apply({'tool':'finish','summary':'done'})

    def test_replay_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=tasks.TASKS[0]; r=execute(t,Reference(t),Path(tmp)/'run',kind='reference')
            self.assertEqual(len(validated(r)[1]),4)
            bad=copy.deepcopy(r); bad['steps'][2]['result']['passed']=False
            with self.assertRaises(ValueError): validated(bad)
            bad=copy.deepcopy(r); bad['split']='test'
            with self.assertRaises(ValueError): validated(bad)

    def test_dataset_excludes_test_and_reference_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for t in tasks.TASKS: execute(t,Reference(t),root/'runs'/t['id'],kind='reference')
            m=build(root/'runs',root/'dataset')
            self.assertEqual(m['counts'],{'train':0,'validation':0})
            m=build(root/'runs',root/'demo',True)
            self.assertEqual(m['counts'],{'train':16,'validation':8})
            self.assertEqual(len(m['rejected']),2)

    def test_network_scope(self):
        for url in ['http://example.com/v1','https://localhost/v1','http://user:pass@localhost/v1']:
            with self.assertRaises(ValueError): Client(url,'x')

    def test_recovery_is_context_only_and_replayed(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=tasks.TASKS[0]; client=Reference(t)
            invalid={'tool':'write','path':'solution.py','content':tasks.source(t,True)}
            client.actions=iter([invalid,*list(client.actions)])
            record=execute(t,client,Path(tmp)/'run',kind='reference')
            self.assertTrue(record['success'])
            with self.assertRaises(ValueError): validated(record)
            _,examples=validated(record,allow_recovery=True)
            self.assertEqual(len(examples),4)
            self.assertEqual(json.loads(examples[0]['messages'][-1]['content'])['tool'],'read')
            self.assertIn('Read before editing',examples[0]['messages'][-2]['content'])
            bad=copy.deepcopy(record); bad['steps'][0]['result']['error']='fabricated error'
            with self.assertRaises(ValueError): validated(bad,allow_recovery=True)

if __name__=='__main__': unittest.main()

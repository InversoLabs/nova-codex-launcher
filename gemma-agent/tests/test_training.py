import unittest
from training.train import tokenize_example
from training.run_pilot_job import ensure_idle

class FakeTokenizer:
    def apply_chat_template(self,messages,tokenize=True,add_generation_prompt=False,**kwargs):
        value=''.join('<'+m['role']+'>'+m['content']+'</>' for m in messages)
        if add_generation_prompt: value+='<assistant>'
        return list(value.encode())

class TrainingTests(unittest.TestCase):
    def test_training_does_not_unload_during_active_work(self):
        ensure_idle([{'status':'COMPLETE'},{'status':'NEEDS_ATTENTION'}])
        for projects in ({},[{'status':'RUNNING'}],[{}]):
            with self.assertRaises((ValueError,RuntimeError)): ensure_idle(projects)
    def test_only_final_action_is_supervised(self):
        row={'messages':[{'role':'user','content':'task'},{'role':'assistant','content':'old action'},
                         {'role':'user','content':'tool result'},{'role':'assistant','content':'new action'}]}
        sample=tokenize_example(FakeTokenizer(),row,1000)
        target=bytes(x for x in sample['labels'] if x!=-100).decode()
        self.assertEqual(target,'new action</>')
        self.assertGreater(sample['labels'].count(-100),0)
        self.assertIsNone(tokenize_example(FakeTokenizer(),row,4))

if __name__=='__main__': unittest.main()

import hashlib
import json
from pathlib import Path
import unittest
from project_corpus.catalog import PROJECTS

class ProjectCorpusTests(unittest.TestCase):
    def test_families_and_fixed_splits(self):
        self.assertEqual(len(PROJECTS),24)
        self.assertEqual(len({p['id'] for p in PROJECTS}),24)
        self.assertEqual({s:sum(p['split']==s for p in PROJECTS) for s in ('train','validation','test')},
                         {'train':16,'validation':4,'test':4})
        for project in PROJECTS:
            self.assertEqual(len(project['cases']),3)
            self.assertIn(project['mutation'][0],project['body'])

    def test_materialized_reference_and_task_hashes(self):
        suite=Path(__file__).resolve().parents[1]/'project_corpus/suite-v2'
        manifest=json.loads((suite/'manifest.json').read_text(encoding='utf-8'))
        for project in manifest['projects']:
            root=suite/'references'/project['id']
            for name,h in project['reference_hashes'].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),h)
            for task in project['tasks']:
                root=suite/'tasks'/task['id']
                for name,h in task['starter_hashes'].items():
                    self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),h)
                self.assertNotIn(project['body'],(root/'TASK.md').read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()

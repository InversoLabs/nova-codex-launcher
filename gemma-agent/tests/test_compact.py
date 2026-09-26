import tempfile
import unittest
from pathlib import Path
from compact_proxy import Adapter,events

class CompactTests(unittest.TestCase):
    def test_write_is_a_codex_patch_not_a_direct_write(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'file.py'; p.write_text('old\n')
            a=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'trace','test')
            item=a.translate({'tool':'write','path':'file.py','content':'new\n'},{'exec_command'})
            self.assertEqual(p.read_text(),'old\n')
            self.assertEqual(item['name'],'exec_command')
            self.assertIn('workspace_tools.py',item['arguments'])
            self.assertEqual(a.calls[item['call_id']]['tool'],'write')
            stream=list(events(item,{},'gemma'))
            self.assertEqual(stream[-1][0],'response.completed')
            self.assertEqual(stream[-1][1]['response']['output'][0],item)

    def test_paths_and_missing_tools_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'trace','test')
            for path in ('../outside','file\n.py','.git/config'):
                with self.assertRaises(ValueError): a.path(path)
            with self.assertRaises(ValueError): a.translate({'tool':'read','path':'file.py'},set())

if __name__=='__main__': unittest.main()

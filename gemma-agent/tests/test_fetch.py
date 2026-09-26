import json
import tempfile
import unittest
from pathlib import Path
from compact_proxy import Adapter
from workspace_tools import DocumentText, fetch_document

class FetchTests(unittest.TestCase):
    def test_server_schema_accepts_fetch_and_paging(self):
        from nova_client import ACTION_SCHEMA
        variants=[v for v in ACTION_SCHEMA['oneOf'] if v['properties']['tool']['const']=='fetch']
        self.assertEqual({tuple(v['required']) for v in variants},{('tool','url'),('tool','url','start')})

    def test_fetch_is_delegated_to_codex(self):
        with tempfile.TemporaryDirectory() as d:
            adapter=Adapter(d,'http://127.0.0.1:18190/v1',Path(d)/'trace','')
            item=adapter.translate({'tool':'fetch','url':'https://example.com/docs/'},{'exec_command'})
            self.assertEqual(item['name'],'exec_command')
            self.assertIn('workspace_tools.py',json.loads(item['arguments'])['cmd'])
            self.assertEqual(list(Path(d).iterdir()),[])

    def test_visible_code_is_preserved(self):
        parser=DocumentText()
        parser.feed('<title>Docs</title><script>hidden()</script><pre>&lt;wa-button&gt;Go&lt;/wa-button&gt;</pre>')
        text=''.join(parser.parts)
        self.assertIn('<wa-button>Go</wa-button>',text)
        self.assertNotIn('hidden()',text)

    def test_non_web_urls_rejected(self):
        for url in ('file:///C:/secret','https://user:pass@example.com/'):
            with self.assertRaises(ValueError): fetch_document({'url':url})

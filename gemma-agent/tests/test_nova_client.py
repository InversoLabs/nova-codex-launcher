import io
import json
import os
import unittest
from unittest.mock import patch
from nova_client import NovaClient,NoRedirect

class NovaTransportTests(unittest.TestCase):
    def test_only_existing_bridge_urls_allowed(self):
        with patch.dict(os.environ,{'NOVA_DESKTOP_API_KEY':'test-only'}):
            for url in ('https://example.com/v1','http://192.168.86.51:8787/v1/other','http://user@127.0.0.1:8788/v1'):
                with self.assertRaises(ValueError): NovaClient(url,'pilot')
            NovaClient('http://127.0.0.1:8788/v1','pilot')
    def test_authenticated_payload_uses_bridge_supported_fields(self):
        with patch.dict(os.environ,{'NOVA_DESKTOP_API_KEY':'test-only'}):
            client=NovaClient('http://127.0.0.1:8788/v1','pilot')
        def respond(req,timeout):
            self.assertEqual(req.get_header('Authorization'),'Bearer test-only')
            body=json.loads(req.data)
            self.assertEqual(body['model'],'pilot')
            self.assertNotIn('chat_template_kwargs',body)
            return io.BytesIO(json.dumps({'choices':[{'message':{'content':'{"tool":"finish","summary":"done"}'}}]}).encode())
        client.http.open=respond
        self.assertIn('finish',client.complete([{'role':'user','content':'hello'}])[0])
        with self.assertRaises(ValueError): NoRedirect().redirect_request(None,None,None,None,None,None)

import unittest
from launch_local import context_model

class ContextTests(unittest.TestCase):
    def test_real_server_profiles_match_context(self):
        base='gemma4-codex:pilot-v1'
        for context,suffix in [(4096,'-4k'),(8192,''),(16384,'-16k'),(32768,'-32k')]:
            self.assertEqual(context_model(base,context),base+suffix)
        self.assertEqual(context_model('custom-model',32768),'custom-model')

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugins/walletfreak/scripts'))
import local,layouts

class Layouts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=layouts.Layouts(self.root,local.read_json,local.atomic_json)
    def test_templates_and_custom_layout_persist_without_private_data(self):
        for t in layouts.CATALOG['templates']:layouts.validate(t['layout'])
        original=self.store.state();value=deepcopy(original['layout']);value['theme']='midnight';value['blocks'].reverse()
        saved=self.store.save({'expected_revision':'empty','layout':value});self.assertEqual(self.store.state(),saved)
        self.assertEqual(self.store.path.stat().st_mode&0o777,0o600)
        self.assertNotEqual(saved['revision'],'empty')
        with self.assertRaisesRegex(ValueError,'changed'):self.store.save({'expected_revision':'empty','layout':value})
    def test_unknown_code_remote_urls_private_values_versions_and_sources_rejected(self):
        base=self.store.state()['layout'];bad=[]
        for key,value in [('version',2),('version',True),('theme','url(https://evil.test)'),('blocks',[]),('title','')]:
            v=deepcopy(base);v[key]=value;bad.append(v)
        for key,value in [('html','<script>bad</script>'),('url','https://evil.test'),('wallet',{'balance':900})]:
            v=deepcopy(base);v[key]=value;bad.append(v)
        for key,value in [('component','remote-code'),('source','credentials.password'),('source','wallet.cards'),('id','../secret')]:
            v=deepcopy(base);v['blocks'][0][key]=value;bad.append(v)
        v=deepcopy(base);v['blocks'].append(deepcopy(v['blocks'][0]));bad.append(v)
        v=deepcopy(base);v['blocks'][0]['script']='alert(1)';bad.append(v)
        for v in bad:
            with self.subTest(v=v),self.assertRaises(ValueError):layouts.validate(v)
        self.assertFalse(self.store.path.exists())
    def test_atomic_failure_and_corrupt_saved_layout_preserve_files(self):
        base=self.store.state()['layout'];self.store.save({'expected_revision':'empty','layout':base});before=self.store.path.read_bytes();revision=self.store.state()['revision']
        with patch.object(self.store,'write',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.store.save({'expected_revision':revision,'layout':base})
        self.assertEqual(self.store.path.read_bytes(),before)
        self.store.path.write_text('{bad json')
        with self.assertRaises(ValueError):self.store.state()
        self.assertEqual(self.store.path.read_text(),'{bad json')

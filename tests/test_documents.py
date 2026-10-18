import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugins/walletfreak/scripts'))
import documents, inventory, local

class References(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.docs=documents.Documents(self.root,local.read_json,local.atomic_json)
    def upload(self,raw=b'%PDF-1.4\nsynthetic test only',name='statement.pdf'):
        return self.docs.upload({'name':name,'content':base64.b64encode(raw).decode()})
    def report(self,state):
        return {'expected_revision':state['revision'],'report':{'title':'Fictional report','generated_at':'2026-10-18T12:00:00Z','metrics':[{'label':'Spending','value':'USD 10.00','detail':'Synthetic example; p1.','source_ids':[state['files'][0]['id']]}],'findings':[]}}
    def test_private_upload_reference_duplicate_and_delete(self):
        state=self.upload();f=state['files'][0];path=Path(f['path']);self.assertTrue(f['available']);self.assertEqual(path.read_bytes(),b'%PDF-1.4\nsynthetic test only');self.assertEqual(path.stat().st_mode&0o777,0o600)
        self.assertEqual(len(self.upload()['files']),1)
        body=self.report(state);self.docs.publish(body)
        state=self.docs.snapshot();self.assertEqual(state['report']['metrics'][0]['value'],'USD 10.00')
        self.docs.delete({'id':f['id'],'expected_revision':state['revision']});self.assertFalse(path.exists());self.assertIsNone(self.docs.state()['report'])
    def test_invalid_uploads_and_disk_failure(self):
        for raw,name in [(b'not pdf','test.pdf'),(b'','test.pdf'),(b'x','../a.csv'),(b'x','a.html'),(b'\xff','a.csv')]:
            with self.assertRaises(ValueError):self.upload(raw,name)
        with patch.object(self.docs,'write',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.upload()
        self.assertEqual(list((self.root/'references').iterdir()),[])
    def test_reports_require_current_revision_and_available_sources(self):
        state=self.upload();report=self.report(state);report['report']['metrics'][0]['source_ids']=['missing']
        with self.assertRaises(ValueError):self.docs.publish(report)
        report=self.report(state);self.upload(b'%PDF-1.4\nsecond','second.pdf')
        with self.assertRaisesRegex(ValueError,'changed'):self.docs.publish(report)
        state=self.docs.snapshot();report=self.report(state);Path(state['files'][0]['path']).unlink()
        with self.assertRaisesRegex(ValueError,'available'):self.docs.publish(report)
    def test_symlinks_and_path_traversal(self):
        outside=self.root/'elsewhere';outside.mkdir();(self.root/'references').symlink_to(outside)
        with self.assertRaisesRegex(ValueError,'symlink'):self.upload()
        with self.assertRaises(ValueError):self.docs.file_path({'file':'../secret.pdf'})
    def test_inventory_filters_marketplace_and_enabled_state(self):
        entries=[{'name':'walletfreak','marketplaceName':'walletfreak','version':'1','enabled':True,'source':{'source':'local','path':str(self.root)}}, {'name':'walletfreak-spending','marketplaceName':'walletfreak','version':'1','enabled':False}, {'name':'unrelated','marketplaceName':'walletfreak','version':'1','enabled':True}, {'name':'walletfreak','marketplaceName':'other','version':'1','enabled':True}]
        with patch.object(inventory.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps({'installed':entries}))),patch.dict('os.environ',{'CODEX_HOME':str(self.root/'codex')}):
            self.assertEqual([p['name'] for p in inventory.discover(self.root)['plugins']],['walletfreak'])
        with patch.object(inventory.subprocess,'run',side_effect=OSError()):self.assertEqual(inventory.discover(self.root)['plugins'],[])

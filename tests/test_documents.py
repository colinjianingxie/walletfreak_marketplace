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
        entries=[{'name':'walletfreak','marketplaceName':'walletfreak','version':'1','enabled':True,'source':{'source':'local','path':str(self.root)}}, {'name':'walletfreak-finance','marketplaceName':'walletfreak','version':'1','enabled':False}, {'name':'unrelated','marketplaceName':'walletfreak','version':'1','enabled':True}, {'name':'walletfreak','marketplaceName':'other','version':'1','enabled':True}]
        with patch.object(inventory.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps({'installed':entries}))),patch.dict('os.environ',{'CODEX_HOME':str(self.root/'codex')}):
            self.assertEqual([p['name'] for p in inventory.discover(self.root)['plugins']],['walletfreak'])
        with patch.object(inventory.subprocess,'run',side_effect=OSError()):self.assertEqual(inventory.discover(self.root)['plugins'],[])

class Archives(References):
    def zip_upload(self, entries):
        import io, zipfile
        data=io.BytesIO()
        with zipfile.ZipFile(data,'w') as archive:
            for name,raw in entries: archive.writestr(name,raw)
        return self.upload(data.getvalue(),'statements.zip')
    def test_archive_inventory_extract_citations_and_cascade(self):
        state=self.zip_upload([('October/one.pdf',b'%PDF-1.4\nexample'),('two.csv',b'Date,Amount\n2026-10-01,10\n'),('readme.txt',b'ignored')])
        parent=state['files'][0];self.assertEqual(len(state['files']),1);self.assertEqual(len(parent['members']),3)
        state=self.docs.extract({'id':parent['id'],'expected_revision':state['revision']});self.assertEqual(len(state['files']),3)
        self.assertEqual(state['files'][1]['member'],'October/one.pdf');self.assertEqual(state['files'][1]['archive_id'],parent['id'])
        again=self.docs.extract({'id':parent['id'],'expected_revision':state['revision']});self.assertEqual(again['revision'],state['revision'])
        body=self.report(state);body['report']['metrics'][0]['source_ids']=[state['files'][1]['id']];self.docs.publish(body)
        state=self.docs.snapshot();self.docs.delete({'id':parent['id'],'expected_revision':state['revision']})
        self.assertEqual(self.docs.state()['files'],[]);self.assertIsNone(self.docs.state()['report']);self.assertEqual(list((self.root/'references').iterdir()),[])
    def test_archive_rejects_traversal_symlinks_limits_and_invalid_members(self):
        import io,zipfile,stat
        for name in ['../x.pdf','/x.pdf','C:/x.pdf','folder\\x.pdf']:
            with self.assertRaises(ValueError):self.zip_upload([(name,b'%PDF-1.4')])
        info=zipfile.ZipInfo('link.pdf');info.external_attr=(stat.S_IFLNK|0o777)<<16
        with self.assertRaises(ValueError):self.zip_upload([(info,b'/etc/passwd')])
        with self.assertRaises(ValueError):self.zip_upload([('nested.zip',b'zip')])
        with self.assertRaises(ValueError):self.zip_upload([(str(i)+'.pdf',b'%PDF-') for i in range(101)])
        state=self.zip_upload([('good.pdf',b'%PDF-1.4'),('bad.csv',b'\xff')]);parent=state['files'][0]
        with self.assertRaises(ValueError):self.docs.extract({'id':parent['id'],'expected_revision':state['revision']})
        self.assertEqual(len(self.docs.state()['files']),1);self.assertEqual(len(list((self.root/'references').iterdir())),1)
    def test_archive_extract_rollback_and_revision(self):
        state=self.zip_upload([('one.pdf',b'%PDF-1.4'),('two.csv',b'a,b')]);body={'id':state['files'][0]['id'],'expected_revision':state['revision']}
        with patch.object(self.docs,'write',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.docs.extract(body)
        self.assertEqual(len(list((self.root/'references').iterdir())),1)
        with self.assertRaises(ValueError):self.docs.extract({**body,'expected_revision':'old'})

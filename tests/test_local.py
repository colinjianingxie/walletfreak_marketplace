import copy
from http.server import HTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch, MagicMock
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'plugins/walletfreak/scripts'))
import local
import browser

def wallet():
    return {'cards':[{'name':'Chase Sapphire Reserve','owner':'Me','notes':'US primary card','reported_on':'2026-10-18'}],
            'programs':[{'name':'MileagePlus','owner':'Me','balance':'50000','approximate':True,'status':'','preserve':True,'reported_on':''}],
            'benefits':[{'name':'Free night','owner':'Me','kind':'certificate','remaining':'1','expires_on':'','notes':'Expiry unknown','reported_on':''}],
            'preferences':'Private preference: preserve my miles'}


def findings():
    return {'title':'Tokyo', 'generated_at':local.now(), 'options':[
        {'id':'cash', 'title':'Cash flight', 'kind':'flight', 'status':'available', 'price':'USD 900', 'observed_at':local.now(), 'sources':[{'label':'Source','url':'https://example.com/flight?session=SECRET'}], 'choice_group':'flight', 'cost':{'cash':'900.10','currency':'USD','complete':True}},
        {'id':'award', 'title':'Award flight', 'kind':'flight', 'status':'available', 'price':'50,000 points + USD 100', 'observed_at':local.now(), 'sources':[{'label':'Source','url':'https://example.com/flight'}], 'choice_group':'flight', 'cost':{'cash':'100.20','currency':'USD','points':50000,'program':'Example Miles','complete':True}},
        {'id':'hotel', 'title':'Hotel', 'kind':'hotel', 'status':'available', 'price':'EUR 200', 'observed_at':local.now(), 'sources':[{'label':'Source','url':'https://example.com/hotel'}], 'choice_group':'stay', 'cost':{'cash':'200.00','currency':'EUR','complete':True}},
        {'id':'unknown', 'title':'Unpriced transfer', 'kind':'transport', 'status':'unverified'}]}


class DataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = local.Store(self.root)
        self.id = self.store.agent_action('publish', {'findings':findings()})['id']

    def save_wallet(self):
        return self.store.user_action('wallet', {'wallet':wallet(), 'expected_revision':self.store.wallet()['revision']})

    def test_publish_selection_totals_and_refresh_preservation(self):
        self.assertNotIn('SECRET', json.dumps(self.store.snapshot()))
        self.store.user_action('selection', {'id':self.id,'shortlist':['cash','award'],'selected':['award','hotel','unknown'],'expected_revision':0})
        totals = local.selected_totals(self.store.trip(self.id))
        self.assertEqual(totals, {'cash':{'USD':'100.20','EUR':'200.00'},'points':{'Example Miles':50000},'unknown':['Unpriced transfer']})
        exported = local.export_findings(self.store.trip(self.id))
        self.assertEqual({i['option_id'] for i in exported['itinerary']}, {'award','hotel','unknown'})
        with self.assertRaises(ValueError):
            self.store.user_action('selection', {'id':self.id,'shortlist':[],'selected':['cash','award'],'expected_revision':1})
        with self.assertRaises(ValueError):
            self.store.agent_action('publish', {'id':self.id,'expected_revision':0,'findings':findings()})
        self.store.agent_action('publish', {'id':self.id,'expected_revision':1,'findings':findings()})
        bad = findings(); bad['options'].pop(1)
        with self.assertRaises(ValueError):
            self.store.agent_action('publish', {'id':self.id,'expected_revision':2,'findings':bad})
        self.assertEqual(local.Store(self.root).trip(self.id)['selected'], ['award','hotel','unknown'])
        if os.name != 'nt':
            self.assertEqual((self.root/'results.json').stat().st_mode & 0o777, 0o600)

    def test_itinerary_visible_without_selection_and_exports_exclude_wallet(self):
        self.save_wallet()
        data = findings()
        data['itinerary'] = [{'when':'Day 1 · local time','title':'Fly to Tokyo','detail':'Proposed flight','option_id':'cash'}]
        self.store.agent_action('publish', {'id':self.id,'expected_revision':0,'findings':data})
        exported = local.export_findings(self.store.trip(self.id))
        self.assertEqual(exported['itinerary'], data['itinerary'])
        self.assertNotIn('Private preference', local.board.render(exported))
        self.assertNotIn('wallet', exported)

    def test_wallet_unknown_dates_and_stale_saves(self):
        self.save_wallet()
        saved = self.store.wallet()
        self.assertEqual(saved['programs'][0]['reported_on'], '')
        self.assertTrue(saved['programs'][0]['approximate'])
        with self.assertRaises(ValueError):
            self.store.user_action('wallet', {'wallet':wallet(),'expected_revision':'empty'})
        self.assertEqual(self.store.wallet(), saved)
        changed = wallet(); changed['programs'][0]['balance']=''
        self.store.user_action('wallet', {'wallet':changed,'expected_revision':saved['revision']})
        self.assertEqual(local.Store(self.root).wallet()['programs'][0]['balance'],'')
        if os.name != 'nt':
            self.assertEqual((self.root/'wallet.json').stat().st_mode & 0o777, 0o600)

    def test_wallet_validation_rejects_credentials_and_invalid_values(self):
        for key, value in [('balance','-1'),('balance','1e8'),('balance',True),('approximate','yes'),('reported_on','2026-02-30')]:
            bad=wallet();bad['programs'][0][key]=value
            with self.subTest(key=key,value=value), self.assertRaises(ValueError): local.validate_wallet(bad)
        for section in ('cards','programs','benefits'):
            bad=wallet();bad[section][0]['password']='secret'
            with self.assertRaises(ValueError): local.validate_wallet(bad)
        bad=wallet();bad['programs'][0]['balance']='0';local.validate_wallet(bad)
        bad=wallet();bad['programs'][0]['balance']='';local.validate_wallet(bad)

    def test_independent_deletion_and_external_file_removal(self):
        self.save_wallet();saved=self.store.wallet()
        with self.assertRaises(ValueError): self.store.user_action('delete-results',{'id':self.id,'expected_revision':99})
        self.store.user_action('delete-results',{'id':self.id,'expected_revision':0})
        self.assertEqual(self.store.snapshot()['trips'],[])
        self.assertEqual(self.store.wallet(),saved)
        with self.assertRaises(ValueError): self.store.agent_action('publish',{'id':self.id,'expected_revision':0,'findings':findings()})
        new_id=self.store.agent_action('publish',{'findings':findings()})['id']
        self.store.user_action('delete-wallet',{'expected_revision':saved['revision']})
        self.assertFalse((self.root/'wallet.json').exists())
        self.assertEqual(self.store.trip(new_id)['id'],new_id)
        self.save_wallet();(self.root/'results.json').unlink()
        self.assertEqual(self.store.snapshot()['trips'],[])
        with self.assertRaises(ValueError): self.store.user_action('selection',{'id':new_id,'shortlist':[],'selected':[],'expected_revision':0})
        self.assertTrue((self.root/'wallet.json').exists())
        self.assertFalse((self.root/'results.json').exists())
        (self.root/'wallet.json').unlink()
        self.assertEqual(self.store.wallet(),local.empty_wallet())

    def test_legacy_migration_and_no_resurrection(self):
        trip=self.store.trip(self.id)
        trip.update(brief={'title':'Original'},brief_revision=1,brief_history=[],findings_brief_revision=1)
        (self.root/'results.json').unlink()
        local.atomic_json(self.root/'state.json',{'version':1,'revision':1,'trips':[trip],'requests':[{'status':'queued'}],'accounts':{}})
        migrated=local.Store(self.root)
        self.assertEqual(migrated.trip(self.id)['findings'],trip['findings'])
        self.assertNotIn('requests',migrated.snapshot())
        self.assertFalse((self.root/'state.json').exists())
        (self.root/'results.json').unlink()
        self.assertEqual(local.Store(self.root).snapshot()['trips'],[])

    def test_atomic_failure_symlinks_and_locks(self):
        self.save_wallet();saved=self.store.wallet()
        with patch('local.os.replace',side_effect=OSError('disk full')):
            with self.assertRaises(OSError): self.save_wallet()
        self.assertEqual(self.store.wallet(),saved)
        target=self.root/'real.json';target.write_text('{}')
        link=self.root/'link.json';link.symlink_to(target)
        with self.assertRaises(ValueError): local.atomic_json(link,{'bad':True})
        self.assertEqual(target.read_text(),'{}')
        with local.exclusive(self.root/'browser.lock'): self.assertTrue(local.browser_active(self.root))
        self.assertFalse(local.browser_active(self.root))


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.server=HTTPServer(('127.0.0.1',0),local.Handler)
        self.server.authority=f'127.0.0.1:{self.server.server_port}'
        self.server.origin='http://'+self.server.authority
        self.server.agent_token='agent-secret'; self.server.ui_token='ui-secret'; self.server.sessions={'session'}
        self.server.store=local.Store(Path(self.temp.name))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def request(self, path, body=None, headers=None):
        h={'Content-Type':'application/json','X-WalletFreak':'1',**(headers or {})}
        request=Request(self.server.origin+path,data=json.dumps(body).encode() if body is not None else None,headers=h)
        try:
            response=urlopen(request,timeout=3)
        except HTTPError as error: response=error
        with response: return response.status,response.headers,response.read()

    def test_auth_origin_privilege_and_private_files(self):
        code, headers, raw = self.request('/assets/brands.json')
        self.assertEqual(code, 200)
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertIn('hilton', json.loads(raw))
        self.assertEqual(self.request('/api/state')[0],401)
        self.assertEqual(self.request('/api/state',headers={'Host':'evil.test'})[0],403)
        self.assertEqual(self.request('/api/wallet',{'wallet':wallet(),'expected_revision':'empty'},headers={'Cookie':'walletfreak=session','Origin':'https://evil.test'})[0],403)
        self.assertEqual(self.request('/api/agent/publish',{},headers={'Cookie':'walletfreak=session'})[0],403)
        self.assertEqual(self.request('/api/session',{'token':'bad'})[0],401)
        code,headers,_=self.request('/api/session',{'token':'ui-secret'})
        self.assertEqual(code,200);self.assertIn('HttpOnly',headers['Set-Cookie']);self.assertIn('SameSite=Strict',headers['Set-Cookie'])
        for path in ('/state.json','/results.json','/wallet.json','/browser-profile/Cookies','/assets/../scripts/local.py','/assets/%2e%2e/scripts/local.py'):
            self.assertEqual(self.request(path,headers={'Cookie':'walletfreak=session'})[0],404)
        code,_,_=self.request('/api/wallet',{'wallet':wallet(),'expected_revision':'empty'},headers={'Cookie':'walletfreak=session'})
        self.assertEqual(code,200)
        code,_,raw=self.request('/api/agent/publish',{'findings':findings()},headers={'Authorization':'Bearer agent-secret'})
        self.assertEqual(code,200)

    def test_vault_api_is_browser_only_and_absent_from_state(self):
        agent={'Authorization':'Bearer agent-secret'}
        self.assertEqual(self.request('/api/vault',headers=agent)[0],403)
        self.assertEqual(self.request('/api/vault/create',{'master_password':'synthetic passphrase'},headers=agent)[0],403)
        code,_,raw=self.request('/api/vault',headers={'Cookie':'walletfreak=session'})
        self.assertEqual(code,200);self.assertEqual(json.loads(raw)['entries'],[])
        self.assertEqual(self.request('/credentials.enc.json',headers={'Cookie':'walletfreak=session'})[0],404)


class BrowserTests(unittest.TestCase):
    def test_modes_forget_and_exclusive_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            self.assertIn('--isolated',browser.launch_args(root,{}))
            settings={'remember':True,'forget':False}
            browser.prepare_profile(root,settings)
            self.assertIn('--user-data-dir',browser.launch_args(root,settings))
            (root/'browser-profile'/'test-session').write_text('fictional')
            (root/'state.json').write_text('{}')
            settings={'remember':False,'forget':True}
            browser.prepare_profile(root,settings)
            self.assertFalse((root/'browser-profile').exists());self.assertTrue((root/'state.json').exists())
            self.assertFalse(local.read_json(root/'settings.json')['forget'])
            (root/'browser-profile').symlink_to(root)
            with self.assertRaises(ValueError): browser.prepare_profile(root,settings)


if __name__=='__main__': unittest.main()

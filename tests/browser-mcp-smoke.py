#!/usr/bin/env python3
"""Opt-in integration check: real Chrome, synthetic loopback cookie, no provider accounts."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'plugins/walletfreak/scripts'))
from local import atomic_json


class Fixture(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'<!doctype html><title>WalletFreak synthetic session test</title><h1>Fictional test only</h1>'
        self.send_response(200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class Client:
    def __init__(self, root, expanded=False):
        plugin=ROOT/'plugins/walletfreak'
        config=json.loads((plugin/'.mcp.json').read_text())['mcpServers']['walletfreak-browser']
        args=[a.replace('${CLAUDE_PLUGIN_ROOT}',str(plugin)) if expanded else a for a in config['args']]
        self.process = subprocess.Popen([sys.executable, *args], cwd=root if expanded else plugin, env={**os.environ, 'WALLETFREAK_DATA':str(root)}, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self.sequence = 0
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.call('initialize', {'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'walletfreak-synthetic-test','version':'1'}})
        self.process.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n')
        self.process.stdin.flush()

    def call(self, method, params):
        self.sequence += 1
        self.process.stdin.write(json.dumps({'jsonrpc':'2.0','id':self.sequence,'method':method,'params':params})+'\n')
        self.process.stdin.flush()
        deadline = time.monotonic()+45
        while time.monotonic()<deadline:
            if self.selector.select(timeout=1):
                line = self.process.stdout.readline()
                if not line:
                    raise RuntimeError('Browser MCP exited: '+self.process.stderr.read()[-500:])
                message=json.loads(line)
                if message.get('id') == self.sequence:
                    if 'error' in message: raise RuntimeError(message['error'])
                    result=message['result']
                    if result.get('isError'): raise RuntimeError(result)
                    return result
        raise TimeoutError(method)

    def tool(self, name, arguments=None):
        return self.call('tools/call', {'name':name,'arguments':arguments or {}})

    def close(self):
        try:
            self.tool('browser_close')
        except RuntimeError:
            pass  # A discovery-only connection may not own the browser.
        finally:
            self.process.terminate()
            self.process.wait(timeout=15)
            self.selector.close()


def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Fixture)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix='walletfreak-mcp-test-') as temporary:
            root=Path(temporary)
            url=f'http://127.0.0.1:{server.server_port}'
            def session(remember, expected, set_cookie=False, forget=False):
                atomic_json(root/'settings.json',{'remember':remember,'forget':forget})
                client=Client(root)
                try:
                    assert 'browser_navigate' in {t['name'] for t in client.call('tools/list',{})['tools']}
                    client.tool('browser_navigate',{'url':url})
                    second=Client(root,expanded=True)
                    try:
                        assert second.call('tools/list',{})['tools'], 'Discovery must not require browser ownership'
                        try:
                            second.tool('browser_navigate',{'url':url})
                        except RuntimeError as error:
                            assert 'WalletFreak browser unavailable' in str(error)
                        else:
                            raise AssertionError('Concurrent browser use must be refused')
                    finally:
                        second.close()
                    result=client.tool('browser_evaluate',{'function':'() => document.cookie'})
                    rendered=json.dumps(result)
                    assert ('walletfreak_fixture=synthetic' in rendered) == expected, rendered
                    if set_cookie:
                        client.tool('browser_evaluate',{'function':"() => { document.cookie = 'walletfreak_fixture=synthetic; Max-Age=3600; SameSite=Strict; Path=/'; return 'Synthetic cookie set'; }"})
                finally:
                    client.close()
            session(False,False,True)
            session(False,False)
            session(True,False,True)
            session(True,True)
            session(False,False,forget=True)
            assert not (root/'browser-profile').exists()
            assert not json.loads((root/'settings.json').read_text())['forget']
            print('Passed: MCP startup/tools, temporary isolation, remembered synthetic session, concurrent discovery with exclusive browser use, and forget-all. No travel accounts accessed.')
    finally:
        server.shutdown();server.server_close();thread.join()


if __name__=='__main__': main()

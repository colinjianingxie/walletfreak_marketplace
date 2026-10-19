#!/usr/bin/env python3
"""Proxy the browser MCP; allow discovery, lock before actual browser use."""
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
from signin import TOOLS, saved_vault, fill_code, redact

from local import atomic_json, data_directory, exclusive, now, read_json


def prepare_profile(root, settings):
    profile = root / 'browser-profile'
    if profile.is_symlink():
        raise ValueError('Refusing a symlink browser profile.')
    if settings.get('forget'):
        singleton = profile / 'SingletonLock'
        if singleton.is_symlink():
            try:
                pid = int(os.readlink(singleton).rsplit('-', 1)[1])
                os.kill(pid, 0)
            except ProcessLookupError:
                pass
            except (ValueError, PermissionError):
                raise ValueError('Close the dedicated WalletFreak Chrome window before forgetting sessions.') from None
            else:
                raise ValueError('Close the dedicated WalletFreak Chrome window before forgetting sessions.')
        if profile.exists():
            shutil.rmtree(profile)
        settings.update(forget=False, remember=False)
        atomic_json(root / 'settings.json', settings)
    if settings.get('remember'):
        profile.mkdir(mode=0o700, exist_ok=True)


def launch_args(root, settings):
    args = [shutil.which('npx') or 'npx', '-y', '@playwright/mcp@0.0.68', '--browser', 'chrome', '--output-mode', 'stdout', '--codegen', 'none']
    return args + (['--user-data-dir', str(root / 'browser-profile')] if settings.get('remember') and not settings.get('forget') else ['--isolated'])


def launch():
    root = data_directory()
    settings = read_json(root / 'settings.json', {'remember': False, 'forget': False})
    if not isinstance(settings, dict) or any(type(settings.get(key, False)) is not bool for key in ('remember', 'forget')):
        raise ValueError('Invalid browser settings. Preserve the file and repair its boolean values.')
    child_env = {k:v for k,v in os.environ.items() if k not in ('DEBUG','PWDEBUG','DEBUG_FILE')}
    process = subprocess.Popen(launch_args(root, settings), env=child_env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, start_new_session=os.name != 'nt')
    output_lock = threading.Lock()
    ownership = None
    discoveries = set()
    sensitive_calls = set()
    secrets = []

    def emit(line):
        with output_lock:
            sys.stdout.write(line)
            sys.stdout.flush()

    def forward():
        for line in process.stdout:
            message=json.loads(line)
            identifier=message.get('id')
            if identifier in discoveries:
                discoveries.discard(identifier)
                if 'result' in message: message['result'].setdefault('tools',[]).extend(TOOLS)
            if identifier in sensitive_calls:
                sensitive_calls.discard(identifier)
                # Discard browser diagnostics, code echoes and snapshots for credential fills.
                parts=message.get('result',{}).get('content',[])
                result_text='\n'.join(p.get('text','').split('### Ran Playwright code')[0] for p in parts)
                success=not message.get('error') and not message.get('result',{}).get('isError') and 'Credentials filled.' in result_text
                message={'jsonrpc':'2.0','id':identifier,'result':{'content':[{'type':'text','text':'Credentials filled on the approved origin. Continue login; ask the user to handle MFA.' if success else 'Could not fill the login fields. Check the origin and empty form; no automatic retry was made.'}], 'isError':not success}}
            emit(json.dumps(redact(message,secrets))+'\n')

    output = threading.Thread(target=forward, daemon=True)
    output.start()

    def interrupted(signum, frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for line in sys.stdin:
            message = json.loads(line)
            # Hosts can use separate discovery and runtime connections. Only tools use the browser.
            if message.get('method') == 'tools/call' and ownership is None:
                candidate = exclusive(root / 'browser.lock')
                acquired = False
                try:
                    candidate.__enter__()
                    acquired = True
                    prepare_profile(root, settings)
                    atomic_json(root / 'browser.json', {'mode': 'remembered' if settings.get('remember') else 'temporary', 'started_at': now()})
                    ownership = candidate
                except (OSError, ValueError) as error:
                    if acquired:
                        candidate.__exit__(None, None, None)
                    emit(json.dumps({'jsonrpc':'2.0','id':message.get('id'),'result':{'isError':True,'content':[{'type':'text','text':f'WalletFreak browser unavailable: {error}. Close the other host’s WalletFreak browser connection before retrying.'}]}})+'\n')
                    continue
            if message.get('method') == 'tools/list': discoveries.add(message.get('id'))
            name=message.get('params',{}).get('name')
            if message.get('method') == 'tools/call' and name in ('walletfreak_signins','walletfreak_sign_in'):
                try:
                    vault=saved_vault(root,read_json,atomic_json)
                    if name=='walletfreak_signins':
                        entries=[{k:r.get(k,'') for k in ('id','provider','label','login_origin')} for r in vault.payload['entries']]
                        emit(json.dumps({'jsonrpc':'2.0','id':message.get('id'),'result':{'content':[{'type':'text','text':json.dumps(entries)}]}})+'\n')
                        continue
                    arguments=message['params'].get('arguments',{})
                    entry=next((r for r in vault.payload['entries'] if r['id']==arguments.get('credential_id')),None)
                    if entry is None:raise ValueError('Saved sign-in no longer exists.')
                    code=fill_code(entry,arguments)
                    secrets.extend([entry['password'],entry['username']])
                    sensitive_calls.add(message.get('id'))
                    message['params']={'name':'browser_run_code','arguments':{'code':code}}
                    line=json.dumps(message)+'\n'
                except (OSError,ValueError) as error:
                    emit(json.dumps({'jsonrpc':'2.0','id':message.get('id'),'result':{'isError':True,'content':[{'type':'text','text':str(error)}]}})+'\n')
                    continue
            process.stdin.write(line)
            process.stdin.flush()
    finally:
        if process.poll() is None:
            if os.name == 'nt':
                process.terminate()
            else:
                os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=15)
            output.join(timeout=5)
        finally:
            if ownership is not None:
                (root / 'browser.json').unlink(missing_ok=True)
                ownership.__exit__(None, None, None)
    return process.returncode


if __name__ == '__main__':
    try:
        sys.exit(launch())
    except (OSError, ValueError) as error:
        print(f'WalletFreak browser unavailable: {error}', file=sys.stderr)
        sys.exit(1)

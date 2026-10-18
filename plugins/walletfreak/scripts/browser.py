#!/usr/bin/env python3
"""Proxy the browser MCP; allow discovery, lock before actual browser use."""
import json
import os
import shutil
import signal
import subprocess
import sys
import threading

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
    process = subprocess.Popen(launch_args(root, settings), stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, start_new_session=os.name != 'nt')
    output_lock = threading.Lock()
    ownership = None

    def emit(line):
        with output_lock:
            sys.stdout.write(line)
            sys.stdout.flush()

    def forward():
        for line in process.stdout:
            emit(line)

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

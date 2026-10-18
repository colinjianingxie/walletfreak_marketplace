"""Read installed plugin metadata and skill documents; never execute skill content."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def skill_description(text):
    match=re.search(r'^description:\s*(.*(?:\n[ \t]+.*)*)',text,re.M)
    if not match: return ''
    value=' '.join(match[1].split()).strip()
    if value.startswith(('>', '|')): value=value[1:].strip()
    if value.startswith('"'):
        try: return json.loads(value)
        except ValueError: pass
    return value.strip("'\"")


def package(root, name, version, enabled=True):
    root=root.resolve()
    skills=[]
    directory=root/'skills'
    if directory.is_dir():
        for path in sorted(directory.glob('*/SKILL.md')):
            if not path.resolve().is_relative_to(root) or path.stat().st_size>200_000: continue
            content=path.read_text()
            skills.append({'name':path.parent.name,'description':skill_description(content),'content':content})
    return {'id':hashlib.sha256(f'{name}:{version}'.encode()).hexdigest()[:12], 'name':name,'version':version,'enabled':enabled,'skills':skills}


def discover(plugin):
    found=[]; note='Enabled WalletFreak plugins in this Codex installation.'
    try:
        run=subprocess.run(['codex','plugin','list','--json'],capture_output=True,text=True,timeout=8,check=True)
        installed=json.loads(run.stdout).get('installed',[])
        base=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))/'plugins/cache'
        for item in installed:
            if item.get('marketplaceName') != 'walletfreak' or item.get('name') not in ('walletfreak', 'walletfreak-spending') or item.get('enabled') is not True: continue
            name,market,version=(item.get(k,'') for k in ('name','marketplaceName','version'))
            if not all(re.fullmatch(r'[A-Za-z0-9_.+@-]+',v) for v in (name,market,version)): continue
            root=base/market/name/version
            if not root.is_dir():
                source=item.get('source',{})
                root=Path(source.get('path','')) if source.get('source')=='local' else root
            if root.is_dir() and root!=Path('.'):
                found.append(package(root,name,version,item.get('enabled',True)))
        if not found: note='No enabled WalletFreak plugins found in local Codex metadata.'
    except (OSError,ValueError,subprocess.SubprocessError):
        note='Enabled WalletFreak plugins could not be verified. Reload to try again.'
    return {'plugins':found,'note':note}

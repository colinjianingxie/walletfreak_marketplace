"""Local statement references and agent-published metrics; uploading never runs analysis."""
import base64
import binascii
from datetime import datetime
import hashlib
import os
from pathlib import Path
import re
import uuid

MAX_FILE = 20_000_000


class Documents:
    def __init__(self, root, read, write):
        self.root, self.read, self.write = root, read, write
        self.path = root / 'documents.json'

    def state(self):
        value = self.read(self.path, {'version': 1, 'revision': 'empty', 'files': [], 'report': None})
        if value.get('version') != 1:
            raise ValueError('Unsupported document store. Preserve the original files.')
        return value

    def file_path(self, entry):
        if not re.fullmatch(r'[a-f0-9]{32}\.(pdf|csv)', entry['file']):
            raise ValueError('Invalid stored file reference.')
        directory = self.root / 'references'
        path = directory / entry['file']
        if directory.is_symlink() or path.is_symlink():
            raise ValueError('Refusing a symlink in statement references.')
        return path

    def snapshot(self):
        state = self.state()
        for entry in state['files']:
            entry['path'] = str(self.file_path(entry))
            entry['available'] = self.file_path(entry).is_file()
        return state

    def upload(self, body):
        if not isinstance(body, dict) or set(body) != {'name', 'content'}:
            raise ValueError('Provide a file name and base64 contents.')
        name = body['name']
        if not isinstance(name, str) or not 1 <= len(name) <= 255 or any(c in name for c in '/\\\x00\r\n'):
            raise ValueError('Invalid file name.')
        suffix = Path(name).suffix.lower()
        if suffix not in ('.pdf', '.csv') or not isinstance(body['content'], str) or len(body['content']) > 27_000_000:
            raise ValueError('Choose a PDF or CSV up to 20 MB.')
        try:
            raw = base64.b64decode(body['content'], validate=True)
        except (ValueError, binascii.Error):
            raise ValueError('Invalid file encoding.') from None
        if not 0 < len(raw) <= MAX_FILE:
            raise ValueError('Choose a nonempty file up to 20 MB.')
        if suffix == '.pdf' and not raw.startswith(b'%PDF-'):
            raise ValueError('The file does not have a PDF header.')
        if suffix == '.csv':
            try: raw.decode('utf-8-sig')
            except UnicodeDecodeError: raise ValueError('Save the CSV as UTF-8 first.') from None
        state = self.state()
        digest = hashlib.sha256(raw).hexdigest()
        if any(f['sha256'] == digest for f in state['files']):
            return self.snapshot()
        if len(state['files']) >= 100 or sum(f['bytes'] for f in state['files']) + len(raw) > 200_000_000:
            raise ValueError('Reference storage is full (100 files / 200 MB). Remove unneeded copies first.')
        identifier = uuid.uuid4().hex
        entry = {'id': identifier, 'name': name, 'file': identifier + suffix, 'bytes': len(raw), 'sha256': digest}
        path = self.file_path(entry)
        path.parent.mkdir(mode=0o700, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'wb') as output:
                output.write(raw); output.flush(); os.fsync(output.fileno())
            state['files'].append(entry)
            state['revision'] = uuid.uuid4().hex
            self.write(self.path, state)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return self.snapshot()

    def delete(self, body):
        state = self.state()
        if not isinstance(body, dict) or set(body) != {'id', 'expected_revision'} or body['expected_revision'] != state['revision']:
            raise ValueError('References changed. Reload before deleting.')
        entry = next((f for f in state['files'] if f['id'] == body['id']), None)
        if entry is None:
            raise ValueError('Reference no longer exists.')
        path = self.file_path(entry)
        state['files'] = [f for f in state['files'] if f['id'] != entry['id']]
        # A report must not outlive the evidence it cites.
        if state['report'] and any(entry['id'] in x['source_ids'] for x in state['report']['metrics'] + state['report']['findings']):
            state['report'] = None
        state['revision'] = uuid.uuid4().hex
        self.write(self.path, state)
        path.unlink(missing_ok=True)
        return self.snapshot()

    def publish(self, body):
        state = self.state()
        if not isinstance(body, dict) or set(body) != {'expected_revision', 'report'} or body['expected_revision'] != state['revision']:
            raise ValueError('References or findings changed. Read references before publishing.')
        report = body['report']
        if not isinstance(report, dict) or set(report) != {'title', 'generated_at', 'metrics', 'findings'}:
            raise ValueError('Provide title, generated_at, metrics and findings.')
        def text(value, maximum):
            if not isinstance(value, str) or not value.strip() or len(value) > maximum:
                raise ValueError('Invalid report text.')
        text(report['title'], 200)
        text(report['generated_at'], 50)
        if datetime.fromisoformat(report['generated_at'].replace('Z', '+00:00')).tzinfo is None:
            raise ValueError('Report time needs a timezone.')
        ids = {f['id'] for f in state['files'] if self.file_path(f).is_file()}
        for key, columns, maximum in [('metrics', {'label', 'value', 'detail', 'source_ids'}, 12), ('findings', {'label', 'detail', 'source_ids'}, 30)]:
            if not isinstance(report[key], list) or len(report[key]) > maximum:
                raise ValueError('Too many report items.')
            for item in report[key]:
                if not isinstance(item, dict) or set(item) != columns:
                    raise ValueError('Invalid report item fields.')
                for field in columns - {'source_ids'}:
                    text(item[field], 2000 if field == 'detail' else 200)
                sources = item['source_ids']
                if not isinstance(sources, list) or not sources or any(not isinstance(i, str) or i not in ids for i in sources):
                    raise ValueError('Every metric and finding must cite available reference IDs.')
        state['report'] = report
        state['revision'] = uuid.uuid4().hex
        self.write(self.path, state)
        return {'revision': state['revision'], 'message': 'Spending findings published to the local dashboard.'}

"""Local statement references and agent-published metrics; uploading never runs analysis."""
import base64
import binascii
from datetime import datetime
import hashlib
import io
import stat
import zipfile
import zlib
from pathlib import PurePosixPath
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
        if not re.fullmatch(r'[a-f0-9]{32}\.(pdf|csv|zip)', entry['file']):
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
        if suffix not in ('.pdf', '.csv', '.zip') or not isinstance(body['content'], str) or len(body['content']) > 27_000_000:
            raise ValueError('Choose a PDF, CSV or ZIP up to 20 MB.')
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
        members = self.archive(raw) if suffix == '.zip' else None
        state = self.state()
        digest = hashlib.sha256(raw).hexdigest()
        if any(f['sha256'] == digest for f in state['files']):
            return self.snapshot()
        if len(state['files']) >= 100 or sum(f['bytes'] for f in state['files']) + len(raw) > 200_000_000:
            raise ValueError('Reference storage is full (100 files / 200 MB). Remove unneeded copies first.')
        identifier = uuid.uuid4().hex
        entry = {'id': identifier, 'name': name, 'file': identifier + suffix, 'bytes': len(raw), 'sha256': digest}
        if members is not None: entry['members'] = members
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

    @staticmethod
    def archive(raw):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                infos = archive.infolist()
                if len(infos) > 100 or sum(i.file_size for i in infos) > 100_000_000:
                    raise ValueError('ZIP limit: 100 entries and 100 MB expanded.')
                members, names = [], set()
                for info in infos:
                    name = info.filename
                    parts = PurePosixPath(name).parts
                    if (not parts or name.startswith('/') or '..' in parts or ':' in name
                            or chr(92) in name or any(ord(c) < 32 for c in name)
                            or len(name) > 255 or name in names
                            or stat.S_ISLNK(info.external_attr >> 16)):
                        raise ValueError('ZIP contains unsafe or duplicate paths.')
                    names.add(name)
                    if info.flag_bits & 1:
                        raise ValueError('Encrypted ZIPs are unsupported. Decrypt locally before uploading.')
                    if info.is_dir(): continue
                    suffix = PurePosixPath(name).suffix.lower()
                    if info.file_size > MAX_FILE or info.file_size > max(info.compress_size, 1) * 200:
                        raise ValueError('ZIP member exceeds size or compression limits.')
                    if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                        raise ValueError('Use a standard stored or deflated ZIP archive.')
                    members.append({'name':name, 'bytes':info.file_size,
                                    'supported':suffix in ('.pdf', '.csv')})
                if not any(m['supported'] for m in members):
                    raise ValueError('ZIP has no PDF or CSV files. Nested archives are not expanded.')
                return members
        except (zipfile.BadZipFile, NotImplementedError) as error:
            raise ValueError('Invalid or unsupported ZIP archive.') from error

    def extract(self, body):
        state = self.state()
        if not isinstance(body, dict) or set(body) != {'id', 'expected_revision'} or body['expected_revision'] != state['revision']:
            raise ValueError('References changed. Read references before extracting.')
        parent = next((f for f in state['files'] if f['id'] == body['id']), None)
        if not parent or not parent['file'].endswith('.zip'):
            raise ValueError('Choose an uploaded ZIP reference.')
        if parent.get('extracted'): return self.snapshot()
        raw = self.file_path(parent).read_bytes()
        existing = {f.get('member') for f in state['files'] if f.get('archive_id') == parent['id']}
        members = [m for m in self.archive(raw) if m['supported'] and m['name'] not in existing]
        if len(state['files']) + len(members) > 100 or sum(f['bytes'] for f in state['files']) + sum(m['bytes'] for m in members) > 200_000_000:
            raise ValueError('Reference storage is full (100 files / 200 MB).')
        pending = []
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                for member in members:
                    with archive.open(member['name']) as source:
                        content = source.read(MAX_FILE + 1)
                    suffix = PurePosixPath(member['name']).suffix.lower()
                    if not content or len(content) > MAX_FILE:
                        raise ValueError('Empty or oversized ZIP member.')
                    if suffix == '.pdf' and not content.startswith(b'%PDF-'):
                        raise ValueError('ZIP member does not have a PDF header.')
                    if suffix == '.csv': content.decode('utf-8-sig')
                    identifier = uuid.uuid4().hex
                    entry = {'id':identifier, 'file':identifier + suffix, 'name':PurePosixPath(member['name']).name,
                             'bytes':len(content), 'sha256':hashlib.sha256(content).hexdigest(),
                             'archive_id':parent['id'], 'archive_name':parent['name'], 'member':member['name']}
                    pending.append((entry, content))
        except (zipfile.BadZipFile, UnicodeDecodeError, RuntimeError, EOFError, zlib.error) as error:
            raise ValueError('Could not read the ZIP contents. No files were extracted.') from error
        written = []
        try:
            for entry, content in pending:
                path = self.file_path(entry)
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                written.append(path)
                with os.fdopen(fd, 'wb') as output:
                    output.write(content); output.flush(); os.fsync(output.fileno())
                state['files'].append(entry)
            parent['extracted'] = True
            state['revision'] = uuid.uuid4().hex
            self.write(self.path, state)
        except Exception:
            for path in written: path.unlink(missing_ok=True)
            raise
        return self.snapshot()

    def delete(self, body):
        state = self.state()
        if not isinstance(body, dict) or set(body) != {'id', 'expected_revision'} or body['expected_revision'] != state['revision']:
            raise ValueError('References changed. Reload before deleting.')
        entry = next((f for f in state['files'] if f['id'] == body['id']), None)
        if entry is None: raise ValueError('Reference no longer exists.')
        removed = [f for f in state['files'] if f['id'] == entry['id'] or f.get('archive_id') == entry['id']]
        ids = {f['id'] for f in removed}
        paths = [self.file_path(f) for f in removed]
        state['files'] = [f for f in state['files'] if f['id'] not in ids]
        for parent in state['files']:
            if parent['id'] == entry.get('archive_id'): parent['extracted'] = False
        if state['report'] and any(ids.intersection(x['source_ids']) for x in state['report']['metrics'] + state['report']['findings']):
            state['report'] = None
        state['revision'] = uuid.uuid4().hex
        self.write(self.path, state)
        for path in paths: path.unlink(missing_ok=True)
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

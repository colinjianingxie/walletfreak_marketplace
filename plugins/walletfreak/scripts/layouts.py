"""Versioned, data-free dashboard layouts. Rendering code always stays bundled locally."""
from copy import deepcopy
import json
from pathlib import Path
import re
import uuid

LIBRARY = Path(__file__).resolve().parents[1] / 'assets/components/v1'
CATALOG = json.loads((LIBRARY / 'catalog.json').read_text())


def validate(layout):
    if not isinstance(layout, dict) or set(layout) != {'version','title','theme','density','blocks'}:
        raise ValueError('Use only version, title, theme, density and blocks.')
    if type(layout['version']) is not int or layout['version'] != 1:
        raise ValueError('Unsupported layout version. This runtime supports v1.')
    if layout['theme'] not in CATALOG['themes'] or layout['density'] not in CATALOG['densities']:
        raise ValueError('Choose a supported theme and density.')
    def title(value):
        if not isinstance(value,str) or not value.strip() or len(value)>120:raise ValueError('Titles must have 1–120 characters.')
    title(layout['title'])
    if not isinstance(layout['blocks'],list) or not 1 <= len(layout['blocks']) <= 12:
        raise ValueError('Choose 1–12 dashboard blocks.')
    ids=set(); components={c['id']:c for c in CATALOG['components']}
    for block in layout['blocks']:
        if not isinstance(block,dict) or set(block) != {'id','component','source','title'}:
            raise ValueError('Blocks accept only id, component, source and title.')
        title(block['title'])
        if not isinstance(block['id'],str) or not re.fullmatch('[a-z][a-z0-9-]{0,39}',block['id']) or block['id'] in ids:
            raise ValueError('Use unique block IDs: lowercase letters, numbers and hyphens.')
        ids.add(block['id'])
        component=components.get(block['component']) if isinstance(block['component'],str) else None
        if component is None or block['source'] not in component['sources']:
            raise ValueError('Unknown component or unsupported data source. Update the plugin for newer components.')
    return deepcopy(layout)


class Layouts:
    def __init__(self, root, read, write):
        self.path,self.read,self.write=root/'layout.json',read,write
    def state(self):
        value=self.read(self.path,{'revision':'empty','layout':CATALOG['templates'][0]['layout']})
        validate(value['layout'])
        return value
    def save(self,body):
        if not isinstance(body,dict) or set(body) != {'expected_revision','layout'}:
            raise ValueError('Provide expected_revision and layout.')
        state=self.state()
        if body['expected_revision'] != state['revision']:
            raise ValueError('Dashboard layout changed. Reload it before saving.')
        layout=validate(body['layout'])
        result={'revision':uuid.uuid4().hex,'layout':layout}
        self.write(self.path,result)
        return result

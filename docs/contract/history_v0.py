"""Read the manifest-and-region contract layout used by the v0.3.6 release.

Each operation receives a reader bound to one source tree: ``read(path)``
returns that tree's text for a repository-relative path and raises when an
input is unavailable. The caller selects the tree and handles its history.
Keep this layout's validation and digest framing stable when current
authoring changes, so released public content remains reproducible.
"""
import hashlib
import json
from pathlib import Path
import re


MANIFEST = 'docs/contract_surfaces.json'


def surfaces(read):
    """Return the selected tree's surface rows after legacy validation."""
    value = json.loads(read(MANIFEST))
    if set(value) != {'surfaces'} or not isinstance(value['surfaces'], list):
        raise ValueError('invalid contract surfaces manifest')
    seen = set()
    suites = json.loads(read('tests/catalog.json'))['suites']
    for row in value['surfaces']:
        if set(row) - {'definitions'} != {'id', 'artifact', 'goldens', 'definition', 'checks'}:
            raise ValueError('invalid surface fields')
        if not re.fullmatch('[a-z][a-z0-9_]*', row['id']) or row['id'] in seen:
            raise ValueError('duplicate or invalid surface id')
        seen.add(row['id'])
        if not row['goldens'] or not row['checks']:
            raise ValueError(f'{row["id"]}: missing golden or verification')
        if any(check not in suites for check in row['checks']):
            raise ValueError(f'{row["id"]}: unknown verification suite')
        for name in [row['definition'], *row['goldens'], *(item.split('#')[0] for item in row.get('definitions', []))]:
            if Path(name).is_absolute() or '..' in Path(name).parts:
                raise ValueError('surface input must be repository-relative')
    return value['surfaces']


def surface_hash(read, row):
    """Hash one legacy row's definition regions and parsed JSON goldens."""
    text = read(row['definition'])
    begin, end = f'<!-- BEGIN CONTRACT {row["id"]} -->', f'<!-- END CONTRACT {row["id"]} -->'
    if text.count(begin) != 1 or text.count(end) != 1 or text.index(begin) >= text.index(end):
        raise ValueError(f'{row["id"]}: expected one ordered definition region')
    definition = ' '.join(text.split(begin)[1].split(end)[0].split())
    for item in row.get('definitions', []):
        name, region = item.split('#')
        prose = read(name)
        start, stop = f'<!-- BEGIN CONTRACT {region} -->', f'<!-- END CONTRACT {region} -->'
        if prose.count(start) != 1 or prose.count(stop) != 1 or prose.index(start) >= prose.index(stop):
            raise ValueError(f'{item}: expected one ordered definition region')
        definition += ' ' + ' '.join(prose.split(start)[1].split(stop)[0].split())
    values = [json.loads(read(name)) for name in row['goldens']]
    data = json.dumps([definition, values], sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(data.encode()).hexdigest()

"""Read the canonical public snapshot carried by tree-authored releases.

Current generation checks this derived view against the authoring tree.
Historical derivation reads the released snapshot and that release's own
goldens. It checks the retained public representation, rather than reparsing
an earlier authoring syntax with today's parser.
"""
import hashlib
import json
from pathlib import PurePosixPath
import re

SNAPSHOT = 'docs/contract/public.json'
FORMAT = 'policywitness.contract.public.v1'
RELEASE = re.compile(r'v[0-9]+\.[0-9]+\.[0-9]+')


def snapshot(read):
    value = json.loads(read(SNAPSHOT))
    if not isinstance(value, dict) or set(value) != {'format', 'history', 'surfaces'}:
        raise ValueError('invalid public contract snapshot')
    if value['format'] != FORMAT or not isinstance(value['surfaces'], list):
        raise ValueError('unsupported public contract snapshot format')
    history = value['history']
    if not isinstance(history, list) or any(not isinstance(tag, str) or not RELEASE.fullmatch(tag) for tag in history):
        raise ValueError('invalid public contract history')
    if len(set(history)) != len(history):
        raise ValueError('duplicate public contract history tag')
    rows, seen = value['surfaces'], set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'id', 'artifact', 'goldens', 'public'}:
            raise ValueError('invalid public surface snapshot fields')
        ident = row['id']
        if not isinstance(ident, str) or not re.fullmatch('[a-z][a-z0-9_]*', ident) or ident in seen:
            raise ValueError('duplicate or invalid public surface id')
        seen.add(ident)
        if not isinstance(row['artifact'], str) or not row['artifact']:
            raise ValueError(f'{ident}: missing public artifact description')
        if not isinstance(row['goldens'], list) or not row['goldens']:
            raise ValueError(f'{ident}: missing canonical shapes')
        for name in row['goldens']:
            if not isinstance(name, str):
                raise ValueError(f'{ident}: shape path must be text')
            path = PurePosixPath(name)
            if name == '.' or path.is_absolute() or '..' in path.parts or path.as_posix() != name:
                raise ValueError(f'{ident}: shape path must be repository-relative')
        if len(set(row['goldens'])) != len(row['goldens']):
            raise ValueError(f'{ident}: duplicate canonical shape')
        if not isinstance(row['public'], (dict, list)) or not row['public']:
            raise ValueError(f'{ident}: missing public content')
    return value


def surfaces(read):
    return snapshot(read)['surfaces']


def surface_hash(read, row):
    shapes = [json.loads(read(name)) for name in row['goldens']]
    payload = [FORMAT, row['public'], shapes]
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()

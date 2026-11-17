"""The bounded development boundary between current owners and the frozen guide.

This is a byte identity, not a second explanation of the product. Publication
readers must derive freshness from source; this record never grants publication.
"""
import hashlib
import json
from pathlib import Path
import sys

WITHHELD = True
GUIDE = 'docs/PolicyWitness.md'
REVISION = '3d3f8e6581d032f1661914271e960604e4298fdc'
SHA256 = '1e886e4ab5ccaf9aa73fe9c7d6e47e87bcf37d3d3c8caf2e093f38bced97d64d'
RECORD = 'Contents/Resources/Evidence/publication.json'


def frozen_guide(root):
    raw = (Path(root) / GUIDE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError('stale PolicyWitness.md: frozen guide differs from ' + REVISION)
    return raw


def record(root, contract):
    frozen_guide(root)
    if not isinstance(contract, str) or not contract.startswith(('development:', 'release:')):
        raise ValueError('publication boundary requires the derived build contract')
    return dict(schema_version=1, status='withheld', reason='frozen_guide',
                build_contract=contract, guide=dict(path=GUIDE, revision=REVISION, sha256=SHA256))


def validate(value, contract):
    expected = dict(schema_version=1, status='withheld', reason='frozen_guide',
                    build_contract=contract, guide=dict(path=GUIDE, revision=REVISION, sha256=SHA256))
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int or value != expected:
        raise ValueError('missing or inconsistent publication boundary evidence')
    return value


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    if sys.argv[1:] != ['--require-publication']:
        raise SystemExit('usage: publication.py --require-publication')
    if WITHHELD is not False:
        raise SystemExit('publication withheld by tagged source: the guide freeze is active')
    print('ok: source permits strict publication freshness verification')

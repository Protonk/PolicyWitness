"""The supplied plist reaches the worker; every binary's read-back is recorded."""
import json
from pathlib import Path
import plistlib
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/fixtures/byoxpc'))
import session
from bundle import command, signature

pw, directory, supplied_path = sys.argv[1:]
out = Path(directory)
supplied = plistlib.loads(Path(supplied_path).read_bytes())
state = json.loads(Path(json.loads((out / 'session.json').read_text())['state_path']).read_text())
bundle = Path(state['bundle_path'])
receipts = out / 'readback'
receipts.mkdir()

# Independent read-back from the installed copy, one binary at a time.
embedded = session.binary_entitlements(bundle, receipts, 'embedded', command)
signatures = {name: signature(bundle / 'Contents/MacOS' / name, receipts / f'signature-{name}') for name in session.HELPERS}
assert embedded['PWRunner'] == supplied, ('host entitlements', embedded['PWRunner'])
assert embedded['pw-probe-runner'] == supplied, \
    ('the worker must hold the supplied entitlements', embedded['pw-probe-runner'])
assert embedded['sb_api_validator'] is None, ('the validator carries no entitlements', embedded['sb_api_validator'])
team = signatures['PWRunner']['TeamIdentifier']
for name in session.HELPERS:
    assert signatures[name]['TeamIdentifier'] == team and not signatures[name]['adhoc'], (name, signatures[name])

# The registry record carries the same read-backs, per binary.
listing = session.registry(pw, receipts, 'registry', command)
record = next(r for r in listing if r['service_name'] == state['service_name'])
(receipts / 'record.json').write_text(json.dumps(record, indent=2) + '\n')
expected_keys = sorted(supplied)
assert record['entitlements']['keys'] == expected_keys and record['entitlements']['error'] is None, record['entitlements']
assert record['worker_entitlements']['keys'] == expected_keys and record['worker_entitlements']['error'] is None, \
    ('the registry must record the worker read-back', record.get('worker_entitlements'))
assert record['validator_entitlements']['keys'] == [] and record['validator_entitlements']['error'] is None, \
    record.get('validator_entitlements')
granted = sorted(key for key, value in supplied.items() if value is True)
for field in ('entitlements', 'worker_entitlements'):
    assert record[field]['granted'] == granted, (field, record[field])
assert record['validator_entitlements']['granted'] == [], record['validator_entitlements']
for field in ('signature', 'worker_signature', 'validator_signature'):
    assert record[field]['team_id'] == team and record[field]['valid'] is True and record[field]['adhoc'] is False, \
        (field, record.get(field))
print(json.dumps(dict(embedded=embedded, team=team, record=record['id'])))

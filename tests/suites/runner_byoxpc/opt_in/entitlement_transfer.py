"""Selection admits the worker that holds the key true; the file effect witnesses it."""
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import contract
from consumer import validate

KEY = 'com.apple.security.cs.allow-jit'
pw, directory = sys.argv[1:]
out = Path(directory)
services = {copy: json.loads((out / copy / 'runner_env.json').read_text())['service_name'] for copy in ('granted', 'denied')}
receipts = {}


def run(name, service, target, *, required=None, code=0):
    policy = (f'(version 1)(allow default)(deny file-write-data (literal "{target}"))'
              f'(allow file-write-data (require-all (literal "{target}") (require-entitlement "{KEY}")))')
    runner = dict(mode='byoxpc', service=service)
    if required is not None:
        runner['required_entitlements'] = required
    spec = dict(schema_version=contract.REQUEST_SCHEMA, specimen_id=name, runner=runner,
                policy=dict(format='sbpl', sbpl_source=policy),
                probe_plan=[dict(step_id='write', sandbox_check=dict(operation='file-write-data', filter=dict(kind='path', value=str(target))),
                                 attempt=dict(kind='file', action='open_write', target=str(target)))])
    path = out / (name + '.specimen.json')
    path.write_text(json.dumps(spec, indent=2) + '\n')
    before = target.read_bytes()
    result = subprocess.run([pw, 'run', str(path), '--no-log-capture', '--timeout-ms', '30000'], capture_output=True, timeout=60)
    (out / (name + '.json')).write_bytes(result.stdout)
    (out / (name + '.stderr')).write_bytes(result.stderr)
    assert result.returncode == code, (name, result.returncode, result.stderr)
    doc = json.loads(result.stdout)
    assert not validate(doc), validate(doc)
    receipts[name] = dict(exit=result.returncode, outcome=doc['result']['normalized_outcome'],
                          before=before.hex(), after=target.read_bytes().hex())
    return doc


with tempfile.TemporaryDirectory(prefix='pw-byoxpc-transfer-', dir='/private/tmp') as temporary:
    # Owned temporary targets, outside any privacy-mediated folder.
    targets = {copy: Path(temporary) / f'{copy}.target' for copy in ('granted', 'denied')}
    for target in targets.values():
        target.write_bytes(b'transfer-original\n')

    # The worker that holds the key true: admitted and the conditioned write completes.
    doc = run('granted-required', services['granted'], targets['granted'], required=[KEY])
    result = doc['data']['runner_result']
    assert result['normalized_outcome'] == 'ok', result
    step = result['steps'][0]
    assert step['sandbox_check']['outcome'] == 'allow' and step['attempt']['outcome'] == 'ok', step
    assert targets['granted'].read_bytes() == b'x', targets['granted'].read_bytes()
    provenance = doc['data']['specimen']['runner_provenance']
    assert provenance['runner_worker_entitlements']['granted'] == [KEY], provenance['runner_worker_entitlements']

    # The worker whose key is present with the value false: refused by name,
    # before any host is reached, and the target is untouched.
    doc = run('denied-required', services['denied'], targets['denied'], required=[KEY], code=2)
    assert doc['result']['normalized_outcome'] == 'tool_error' and doc['data'].get('runner_result') is None, doc['result']
    error = doc['result']['error']
    assert 'worker' in error and KEY in error and 'other than true' in error, error
    assert doc['data']['specimen']['runner_provenance'] is None, doc['data']['specimen']
    assert targets['denied'].read_bytes() == b'transfer-original\n'

    # Without a requirement the same runner is admitted, and the kernel does
    # not grant the false-valued key: the conditioned write is denied.
    doc = run('denied-plain', services['denied'], targets['denied'])
    result = doc['data']['runner_result']
    assert result['normalized_outcome'] == 'ok', result
    step = result['steps'][0]
    assert step['sandbox_check']['outcome'] == 'deny' and step['attempt']['outcome'] == 'open_failed', step
    assert targets['denied'].read_bytes() == b'transfer-original\n'
    provenance = doc['data']['specimen']['runner_provenance']
    assert provenance['runner_worker_entitlements']['keys'] == [KEY], provenance['runner_worker_entitlements']
    assert provenance['runner_worker_entitlements']['granted'] == [], provenance['runner_worker_entitlements']

(out / 'receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
print(json.dumps(receipts))

"""Compare extension envelopes with independent installed-binary read-backs."""
import json
from pathlib import Path
import sys

out = Path(sys.argv[1])
state = json.loads((out / 'session.json').read_text())
record = json.loads((out / 'readback/record.json').read_text())
count = 0
for directory in ('extensions', 'phases'):
    for path in (out / directory).rglob('run.json'):
        envelope = json.loads(path.read_text())
        provenance = envelope['data']['specimen']['runner_provenance']
        assert provenance['runner_kind'] == 'byoxpc'
        assert provenance['runner_registry_id'] == record['id'] == state['runner_id']
        assert provenance['runner_service_name'] == state['service_name']
        assert provenance['runner_bundle_path'] == state['bundle_path']
        for role in ('worker', 'issuer', 'validator'):
            for kind in ('signature', 'entitlements'):
                key = role + '_' + kind
                assert provenance['runner_' + key] == record[key], (path, key)
        result = envelope['data']['runner_result']
        for declaration in result.get('extensions') or []:
            issuer = declaration.get('issuer')
            if issuer:
                assert issuer['executable_path'] == str(Path(state['bundle_path']) / 'Contents/MacOS/pw-extension-issuer')
                assert issuer['pid'] != result['runner_subprocess']['pid']
        count += 1
assert count > 0
print(f'{count} envelopes agree with the installed runner and independent issuer/worker read-backs.')

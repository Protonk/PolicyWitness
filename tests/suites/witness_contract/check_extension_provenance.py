"""Compare extension envelopes with independent installed-binary read-backs."""
import json
import hashlib
from pathlib import Path
import sys

out = Path(sys.argv[1])
state = json.loads((out / 'session.json').read_text())
record = json.loads((out / 'readback/record.json').read_text())
count = 0
for directory in ('extensions', 'directory', 'phases', 'maximum'):
    for path in (out / directory).rglob('run.json'):
        envelope = json.loads(path.read_text())
        provenance = envelope['data']['specimen']['runner_provenance']
        assert provenance['runner_kind'] == 'byoxpc'
        assert provenance['runner_registry_id'] == record['id'] == state['runner_id']
        assert provenance['runner_service_name'] == state['service_name']
        assert provenance['runner_bundle_path'] == state['bundle_path']
        assert provenance['runner_issuer_entitlements']['granted'] == []
        binary = envelope['data']['specimen']['binaries']['issuer']
        request = json.loads((path.parent / 'specimen.json').read_text())
        override = request.get('_test_overrides', {}).get('issuer_executable_path')
        issuer_path = Path(override) if override else Path(state['bundle_path']) / 'Contents/MacOS/pw-extension-issuer'
        assert binary['path'] == str(issuer_path)
        actual = hashlib.sha256(issuer_path.read_bytes()).hexdigest() if issuer_path.is_file() else None
        assert binary['actual_sha256'] == actual
        expected = 'unavailable' if actual is None else 'match' if actual == binary['baseline_sha256'] else 'mismatch'
        assert binary['verification'] == expected
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

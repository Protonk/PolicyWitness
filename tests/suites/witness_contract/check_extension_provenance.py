"""Compare actor/ordinary envelopes with independently read installed equipment."""
import hashlib
import json
from pathlib import Path
import plistlib
import sys

out = Path(sys.argv[1])
state = json.loads((out / 'session.json').read_text())
record = json.loads((out / 'readback/record.json').read_text())
bundle = Path(state['bundle_path'])
roles = {'worker': 'pw-probe-runner', 'unentitled_worker': 'pw-probe-runner-unentitled', 'validator': 'sb_api_validator'}
count = 0
for directory in ('extensions', 'directory', 'phases', 'maximum', 'redelegation', 'equipment', 'actor-inherited-restriction'):
    for path in (out / directory).rglob('run.json'):
        envelope = json.loads(path.read_text())
        provenance = envelope['data']['specimen']['runner_provenance']
        assert provenance['runner_kind'] == 'byoxpc'
        assert provenance['runner_registry_id'] == record['id'] == state['runner_id']
        assert provenance['runner_service_name'] == state['service_name']
        assert provenance['runner_bundle_path'] == state['bundle_path']
        assert provenance['runner_unentitled_worker_entitlements']['granted'] == []
        request = json.loads((path.parent / 'specimen.json').read_text())
        for role, filename in roles.items():
            binary = envelope['data']['specimen']['binaries'][role]
            override = request.get('_test_overrides', {}).get(role + '_executable_path') if role in ('worker', 'validator') else None
            selected = Path(override) if override else bundle / 'Contents/MacOS' / filename
            if selected.is_file():
                assert Path(binary['path']).samefile(selected), (path, role, binary['path'], selected)
            else:
                # Keep unavailable-artifact checks without requiring an inode;
                # existing parent aliases may still resolve to the same path.
                assert Path(binary['path']).resolve() == selected.resolve(), (path, role, binary['path'], selected)
                assert not Path(binary['path']).is_file(), (path, role, binary['path'])
            actual = hashlib.sha256(selected.read_bytes()).hexdigest() if selected.is_file() else None
            assert binary['actual_sha256'] == actual
            expected = 'unavailable' if actual is None else 'match' if actual == binary['baseline_sha256'] else 'mismatch'
            assert binary['verification'] == expected
            for kind in ('signature', 'entitlements'):
                key = role + '_' + kind
                assert provenance['runner_' + key] == record[key], (path, key)
        result = envelope['data']['runner_result']
        assert 'extensions' not in result
        if result.get('execution_form') == 'actors':
            # References are positions in these two tables.
            bindings, entitlements = result['equipment_bindings'], result['equipment_entitlements']
            for actor in result['actors']:
                equipment = actor['equipment']
                binding = bindings[equipment['binding_ref']]
                assert binding['sha256'] == hashlib.sha256(Path(binding['path']).read_bytes()).hexdigest()
                if binding['source'] == 'packaged':
                    expected = bundle / 'Contents/MacOS' / ('pw-probe-runner-unentitled' if equipment['resolved'] == 'unentitled' else 'pw-probe-runner')
                    assert Path(binding['path']).samefile(expected) and binding['implementation_identity'] == 'inventory_verified', (path, binding, expected)
                else:
                    assert binding['source'] == 'test_override' and binding['implementation_identity'] == 'unverified_fixture'
                    assert binding.get('relative_path') is None and binding.get('expected_sha256') is None
                execution = equipment['execution']
                if execution['status'] == 'matched':
                    assert execution['pid'] == actor['launch']['pid'] == actor['subprocess']['pid']
                    assert Path(execution['path']).samefile(binding['path']) and execution['cdhash'] == binding['cdhash'], (path, execution, binding)
                    static = entitlements[binding['entitlements_ref']]
                    live = entitlements[execution['entitlements_ref']]
                    assert live['source'] == 'execution' and live['actor_id'] == actor['actor_id'] and live['binding_ref'] == equipment['binding_ref']
                    assert plistlib.loads(live['raw_plist'].encode()) == plistlib.loads(static['raw_plist'].encode())
        count += 1
assert count > 0
print(f'{count} envelopes retain installed artifact, actor binding and live code observations separately.')

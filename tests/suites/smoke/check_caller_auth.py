"""Require an authorization-dependent result from real built-in XPC traffic."""
import json
from pathlib import Path
import plistlib
import secrets
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'fixtures/caller_auth'))
from bundle import CLIENT, SERVICE, candidate, cleanup_processes, command, digest, inventory, prepare, save, signature
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from blackbox import validate_step


def call(fixture, work, label, *, authorized=False, service=None):
    out = fixture['out'] / label
    out.mkdir()
    target = work / secrets.token_hex(16)
    seed = secrets.token_bytes(64)
    target.write_bytes(seed)
    (out / 'before.bin').write_bytes(seed)
    spec = {'schema_version': 1, 'specimen_id': secrets.token_hex(16),
            'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'},
            'probe_plan': [{'step_id': secrets.token_hex(16),
                           'sandbox_check': {'operation': 'file-write-data',
                                             'filter': {'kind': 'path', 'value': str(target)}},
                           'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(target)}}]}
    save(out / 'specimen.json', spec)
    request = work / (spec['specimen_id'] + '.json')
    save(request, spec)
    client = fixture['authorized_client'] if authorized else fixture['client']
    meta = command(out / 'client', [client, 'run', '--timeout-ms', '5000',
                   service or fixture['service'], request], timeout=10, check=False)
    after = target.read_bytes()
    (out / 'after.bin').write_bytes(after)
    result = json.loads((out / 'client/stdout').read_text())
    # Both actual XPC replies and the client's locally generated error replies
    # use the response-5 contract. No process status is invented on rejection.
    assert result['schema_version'] == 5, result
    for step in result['steps']:
        assert 'deny_signal' in step and step['deny_signal'] is None, step
    observation = {'command': meta, 'result': result, 'specimen': spec,
                   'service': service or fixture['service'], 'changed': after != seed,
                   'nonempty': bool(after), 'client_sha256': digest(client)}
    save(out / 'observation.json', observation)
    return observation


def accepted(observation):
    result, spec = observation['result'], observation['specimen']
    assert observation['command']['returncode'] == 0, observation
    assert observation['changed'] and observation['nonempty'], 'accepted request left no file effect'
    assert result['normalized_outcome'] == 'ok' and result['rc'] == 0, result
    assert result['specimen_id'] == spec['specimen_id'] and result['bundle_id'] == observation['service'], result
    assert result.get('test_overrides') is None and len(result['steps']) == 1, result
    step = result['steps'][0]
    assert step['step_id'] == spec['probe_plan'][0]['step_id'], step
    assert step['attempt']['requested_path'] == spec['probe_plan'][0]['attempt']['target'], step
    errors = validate_step(step, {'sandbox_outcome': 'allow', 'attempt_ok': True, 'errno': None})
    assert not errors, errors


def rejection_errors(observation):
    """A transport failure alone is not proof; the live paired controls are required too."""
    errors = []
    result, meta = observation['result'], observation['command']
    if meta['returncode'] == 0 or result.get('normalized_outcome') == 'ok':
        errors.append('request_completed')
    if observation['changed']:
        errors.append('file_changed')
    if 'request_completed' in errors:
        return errors
    if meta['returncode'] != 1 or result.get('normalized_outcome') != 'xpc_error':
        errors.append('equipment: expected bounded XPC invalidation, not crash or timeout')
    error = result.get('error') or ''
    # Cocoa reports rejected connections as interrupted (4097) or invalidated
    # (4099). Neither code establishes authorization without the paired calls.
    if (not any(f'NSCocoaErrorDomain:{code} ' in error for code in (4097, 4099))
            or observation['service'] not in error or 'lookup' in error.lower()
            or 'Sandbox restriction' in error or 'No such process' in error):
        errors.append('equipment: connection did not establish a rejection-capable route')
    if (meta['elapsed_seconds'] >= 5 or result.get('steps') != [] or result.get('rc') != 1
            or result.get('runner_subprocess') is not None):
        errors.append('equipment: late response or unexpected attempt evidence')
    return errors


def main():
    source, out = map(lambda p: Path(p).resolve(), sys.argv[1:3])
    identity = sys.argv[3]
    before = inventory(source)
    save(out / 'source-before.json', before)
    try:
        source_signatures = {name: signature(source / path, out / ('source-' + name))
                             for name, path in (('client', CLIENT), ('service', SERVICE), ('app', Path('.')))}
        original = source_signatures['client']
        assert original['TeamIdentifier'] not in ('', 'not set') and not original['adhoc'], original
        for key, sig in source_signatures.items():
            assert sig['runtime'] and not sig['adhoc'], (key, sig)
            assert sig['TeamIdentifier'] == original['TeamIdentifier'], (key, sig)
        info = plistlib.loads((source / SERVICE / 'Contents/Info.plist').read_bytes())
        assert info.get('PWRunnerRequireSignedCaller') is True, 'selected runner has caller auth disabled'
        assert original['Identifier'] in info['PWRunnerAllowedIdentifiers'], info
        mismatch_id = 'com.policywitness.test.disallowed'
        assert mismatch_id not in info['PWRunnerAllowedIdentifiers'], info
        with tempfile.TemporaryDirectory(prefix='pw-caller-auth-', dir='/private/tmp') as temporary:
            work = Path(temporary)
            save(out / 'staging.json', {'path': str(work)})
            rejected = []
            try:
                # Exercise the selected, unmodified signing arrangement first:
                # re-signing a fixture must not repair a broken source app for us.
                selected_out = out / 'selected-app'
                selected_out.mkdir()
                accepted(call({'client': source / CLIENT, 'out': selected_out,
                               'service': info['CFBundleIdentifier']}, work, 'accepted'))
                mismatch = candidate(source, work, out / 'candidate-mismatch', identity, mismatch_id)
                adhoc = candidate(source, work, out / 'candidate-adhoc', '-', original['Identifier'])
                fixtures = {}
                for name, client, options in (
                        ('original', source / CLIENT, {}),
                        ('mismatch-restricted', mismatch, {}),
                        ('mismatch-relaxed', mismatch, {'allow_identifier': mismatch_id}),
                        ('adhoc-restricted', adhoc, {}),
                        ('adhoc-relaxed', adhoc, {'auth_off': True})):
                    fixture = prepare(source, work, out / name, identity, client, **options)
                    fixtures[name] = fixture
                    metadata = {key: signature(path, out / name / ('signature-' + key))
                                for key, path in (('client', fixture['client']),
                                                  ('service', fixture['app'] / SERVICE),
                                                  ('app', fixture['app']))}
                    for key, sig in metadata.items():
                        assert sig['runtime'], (name, key, sig)
                        assert sig['entitlements'] == source_signatures[key]['entitlements'], (name, key, sig)
                        expected_adhoc = key == 'client' and name.startswith('adhoc')
                        assert sig['adhoc'] == expected_adhoc, (name, key, sig)
                        assert sig['TeamIdentifier'] == ('not set' if expected_adhoc else original['TeamIdentifier']), sig
                        if not expected_adhoc:
                            assert sig.get('Timestamp'), (name, key, 'trusted timestamp missing')
                    assert metadata['client']['Identifier'] == (mismatch_id if name.startswith('mismatch') else original['Identifier'])
                    assert metadata['service']['Identifier'] == fixture['service']
                    assert metadata['app']['Identifier'] == fixture['app_id']
                accepted(call(fixtures['original'], work, 'accepted'))
                controls = {}
                for kind in ('mismatch', 'adhoc'):
                    restricted, relaxed = fixtures[kind + '-restricted'], fixtures[kind + '-relaxed']
                    assert digest(restricted['client']) == digest(relaxed['client']), 'paired clients differ'
                    positive = call(relaxed, work, 'accepted')
                    accepted(positive)
                    # Feed the actual relaxed-policy run to the rejection checker:
                    # disabling the restriction must make that contract fail.
                    controls[kind + '-relaxed-as-rejected'] = rejection_errors(positive)
                    assert {'request_completed', 'file_changed'} <= set(controls[kind + '-relaxed-as-rejected'])
                    negative = call(restricted, work, 'rejected')
                    errors = rejection_errors(negative)
                    save(restricted['out'] / 'rejection-errors.json', errors)
                    assert not errors, (kind, errors, negative)
                    rejected.append((restricted['out'] / 'rejected',
                                     Path(negative['specimen']['probe_plan'][0]['attempt']['target'])))
                    accepted(call(restricted, work, 'authorized-after-rejection', authorized=True))
                missing = call(fixtures['original'], work, 'missing-service',
                               service='com.policywitness.test.missing.s' + secrets.token_hex(12))
                assert missing['result']['normalized_outcome'] == 'xpc_error' and not missing['changed'], missing
                controls['missing-service-as-rejected'] = rejection_errors(missing)
                assert any(e.startswith('equipment:') for e in controls['missing-service-as-rejected']), controls
                save(out / 'controls.json', controls)
            finally:
                cleanup_processes(work, out)
                # Recheck after every fixture process has stopped, so delayed
                # execution cannot hide behind an early failed client response.
                for call_out, target in rejected:
                    final = target.read_bytes()
                    (call_out / 'final.bin').write_bytes(final)
                    assert final == (call_out / 'before.bin').read_bytes(), 'rejected request wrote late'
    finally:
        after = inventory(source)
        save(out / 'source-after.json', after)
        assert before == after, 'caller-auth tests modified the selected app'
    print('Both caller restrictions enforced; identical-byte positive controls and independent file effects verified')


if __name__ == '__main__':
    main()

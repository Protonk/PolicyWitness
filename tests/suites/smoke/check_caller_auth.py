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
import consumer
import contract
from blackbox import validate_step
from runner_client_capture import validate_capture, host_reply


def call(fixture, work, label, *, authorized=False, service=None):
    out = fixture['out'] / label
    out.mkdir()
    target = work / secrets.token_hex(16)
    seed = secrets.token_bytes(64)
    target.write_bytes(seed)
    (out / 'before.bin').write_bytes(seed)
    spec = {'schema_version': contract.REQUEST_SCHEMA, 'specimen_id': secrets.token_hex(16),
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
    capture = json.loads((out / 'client/stdout').read_text())
    assert not validate_capture(capture), validate_capture(capture)
    # Client transport observations carry no synthetic host result. Only exact
    # received host bytes are admitted under the response schema.
    result = host_reply(capture) if capture['terminal'] == 'runner_reply' else None
    if capture['terminal'] == 'runner_reply':
        assert not consumer.validate(result), consumer.validate(result)
    observation = {'command': meta, 'capture': capture, 'result': result, 'specimen': spec,
                   'service': service or fixture['service'], 'changed': after != seed,
                   'nonempty': bool(after), 'client_sha256': digest(client)}
    save(out / 'observation.json', observation)
    return observation


def accepted(observation):
    result, spec = observation['result'], observation['specimen']
    capture = observation['capture']
    assert observation['command']['returncode'] == 0, observation
    assert capture['terminal'] == 'runner_reply' and capture['submission']['state'] == 'invoked', capture
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
    result, meta, capture = observation['result'], observation['command'], observation['capture']
    if meta['returncode'] == 0 or capture['terminal'] == 'runner_reply':
        errors.append('request_completed')
    if observation['changed']:
        errors.append('file_changed')
    if 'request_completed' in errors:
        return errors
    if (meta['returncode'] != 1 or meta['harness_timeout'] or capture['terminal'] != 'xpc_timeout'
            or capture['acquisition_stop'] != 'overall_deadline' or capture['timeout_ms'] != 5000):
        errors.append('equipment: expected bounded acquisition deadline after XPC rejection')
    if (capture['submission']['state'] != 'not_invoked' or result is not None
            or capture.get('runner_reply') is not None or capture.get('submission_refusal') is not None):
        errors.append('equipment: unexpected submission or host reply')
    attempts = capture['attempts']
    if (not attempts or any(attempt['outcome'] not in ('transport_error', 'timeout')
                            or attempt.get('control') is not None for attempt in attempts)):
        errors.append('equipment: unexpected acquisition or admitted control')
    native_errors = [attempt['error'] for attempt in attempts if isinstance(attempt.get('error'), dict)]
    # Cocoa reports rejected connections as interrupted (4097) or invalidated
    # (4099). The terminal observation is now the overall deadline; native
    # diagnostics remain in the acquisition attempts. Neither a code nor a
    # deadline establishes authorization without the paired live calls.
    def complete_route(error):
        return (error.get('stage') == 'acquisition'
                and error.get('domain') == 'NSCocoaErrorDomain' and error.get('code') in (4097, 4099)
                and error.get('domain_truncated') is False and error.get('message_truncated') is False
                and observation['service'] in error.get('message', ''))

    def excluded_route(error):
        message = error.get('message', '').lower()
        return (error.get('domain_truncated') is True or error.get('message_truncated') is True
                or any(text in message for text in ('lookup', 'sandbox restriction', 'no such process')))

    if not any(complete_route(error) for error in native_errors) or any(excluded_route(error) for error in native_errors):
        errors.append('equipment: connection did not establish a rejection-capable route')
    # validate_capture checks the continuous-clock deadline evidence. The
    # subprocess watchdog bounds collection; consuming five seconds is expected.
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
                assert (missing['capture']['terminal'] == 'xpc_timeout'
                        and missing['capture']['acquisition_stop'] == 'overall_deadline'
                        and missing['capture']['submission']['state'] == 'not_invoked'
                        and missing['result'] is None and not missing['changed']), missing
                controls['missing-service-as-rejected'] = rejection_errors(missing)
                assert ('equipment: connection did not establish a rejection-capable route'
                        in controls['missing-service-as-rejected']), controls
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

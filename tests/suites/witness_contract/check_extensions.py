"""Real extension lifecycle and fresh-descriptor observations through the CLI."""
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'docs'))
import markdown_reader  # noqa: E402
import consumer
from contract import REQUEST_SCHEMA
from run_capture import RunCapture


def probe(identity, target):
    return {'step_id': identity, 'sandbox_check': {'operation': 'file-read-data',
            'filter': {'kind': 'path', 'value': str(target)}},
            'attempt': {'kind': 'file', 'action': 'read_fresh', 'target': str(target)}}


def intervention(identity, operation):
    value = {'operation': operation, 'handle_ref': 'handle'}
    if operation == 'consume':
        value['token_ref'] = 'token'
    return {'step_id': identity, 'extension': value}


def specimen(target, phases):
    return {'schema_version': REQUEST_SCHEMA, 'specimen_id': 'extensions',
            'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)(deny file-read-data)(allow file-read-data (extension "com.apple.app-sandbox.read"))'},
            'extensions': [{'token_ref': 'token', 'target': str(target)}],
            'phases': [{'phase_id': f'p{i}', 'actions': actions} for i, actions in enumerate(phases)]}


def capture(pw, out, name, spec, *, expected_rc=0, session_state=None):
    directory = out / name
    if session_state:
        spec['runner'] = {'mode': 'byoxpc', 'service': session_state['service_name']}
        directory.mkdir(parents=True, exist_ok=True)
    with RunCapture(pw, directory, spec, cli_args=[]) as captured:
        assert captured.wait(timeout=40) == expected_rc, captured.metadata_path
        envelope = captured.load_json()
    errors = consumer.validate(envelope)
    assert not errors, errors
    from lifecycle_oracle import check_record
    errors = check_record(envelope)
    assert not errors, errors
    return envelope, envelope['data']['runner_result']


def run_suite(pw, out, session_state=None):
    out.mkdir(parents=True, exist_ok=True)
    if session_state:
        target_dir = Path(session_state['staging']) / 'extension-targets'
        return run_targets(pw, out, target_dir, session_state)
    with tempfile.TemporaryDirectory(prefix='pw-extension-targets-', dir='/private/tmp') as directory:
        return run_targets(pw, out, Path(directory), session_state)


def run_targets(pw, out, target_dir, session_state):
    target_dir.mkdir(parents=True, exist_ok=True)
    (out / 'target-directory.json').write_text(json.dumps({'path': str(target_dir),
        'ownership': 'byoxpc_session' if session_state else 'temporary_directory'}) + '\n')
    target = target_dir / 'extension-target'
    contents = b'PW extension fresh read witness\n'
    target.write_bytes(contents)
    metadata = target.stat()
    spec = specimen(target, [[probe('before', target), intervention('consume', 'consume')],
                             [probe('during', target), intervention('release', 'release')],
                             [probe('after', target)]])
    envelope, runner = capture(pw, out, 'lifecycle', spec, session_state=session_state)
    assert runner['normalized_outcome'] == 'ok', runner
    assert runner['sandboxed_after_apply'] and runner['runner_subprocess']['reaped']
    declaration, = runner['extensions']
    assert declaration['preparation_status'] == 'prepared'
    assert declaration['identity']['inode'] == metadata.st_ino
    assert declaration['identity']['device'] == metadata.st_dev
    assert declaration['issuance_status'] == 'issued' and declaration['delivery_status'] == 'delivered'
    issuer = declaration['issuer']
    assert issuer['native_nonnull'] and issuer['result_published'] and issuer['call_boundary_observed']
    assert issuer['reaped'] and issuer['exit_code'] == 0 and issuer['euid'] == os.geteuid()
    assert issuer['pid'] != runner['runner_subprocess']['pid']
    consume, release = runner['extension_events']
    assert consume['native_result'] != -1 and consume['status'] == 'returned'
    assert release['native_result'] == 0 and release['status'] == 'returned'
    assert consume['handle_ref'] == release['handle_ref'] == 'handle'
    before, during, after = [x['attempt'] for x in runner['steps']]
    assert before['rc'] != 0
    # A successful release does not itself require access revocation.
    if after['rc'] == 0:
        assert bytes.fromhex(after['fresh_read']['content_hex']) == contents
    read = during['fresh_read']
    assert during['rc'] == 0 and read['open_rc'] >= 0 and read['close_rc'] == 0
    assert bytes.fromhex(read['content_hex']) == contents and read['read_rc'] == len(contents)
    assert read['identity']['inode'] == metadata.st_ino and read['identity']['device'] == metadata.st_dev
    assert all(x['comparison']['order'] == 'query_first' for x in runner['steps'])
    assert all(p['arrival_observed'] and p['completion_observed'] for p in runner['phases'])
    assert target.read_bytes() == contents
    # Execute the public example's actual JSON, preserving its phase/action names.
    heredoc = 'cat > "$PW_EXTENSION_DIR/request.json" <<JSON\n'
    fences = [block.content for block in markdown_reader.read(ROOT / 'docs/PolicyWitness.md').fences() if heredoc in block.content]
    assert len(fences) == 1, f'expected one fenced example writing the extension request; found {len(fences)}'
    example = fences[0].split(heredoc, 1)[1].split('\nJSON\n', 1)[0]
    request = json.loads(example.replace('$PW_EXTENSION_DIR/target', str(target)))
    _, documented = capture(pw, out, 'guide_example', request, session_state=session_state)
    assert documented['extensions'][0]['issuance_status'] == 'issued'
    assert documented['extensions'][0]['delivery_status'] == 'delivered'
    consumed, released = documented['extension_events']
    assert consumed['status'] == released['status'] == 'returned'
    assert consumed['native_result'] != -1 and released['native_result'] == 0
    assert documented['steps'][0]['attempt']['rc'] != 0
    guide_during = documented['steps'][1]['attempt']
    assert guide_during['rc'] == 0 and bytes.fromhex(guide_during['fresh_read']['content_hex']) == contents
    after_example = documented['steps'][2]['attempt']
    if after_example['rc'] == 0:
        assert bytes.fromhex(after_example['fresh_read']['content_hex']) == contents
    assert all(step['comparison']['order'] == 'query_first' for step in documented['steps'])
    assert target.read_bytes() == contents
    (out / 'independent-observations.json').write_text(json.dumps({'device': metadata.st_dev,
        'inode': metadata.st_ino, 'content_hex': contents.hex(), 'unchanged_contents': True}, indent=2) + '\n')
    for size in (63, 64, 65):
        bounded = target_dir / f'read-{size}'
        payload = bytes(range(size))
        bounded.write_bytes(payload)
        request = specimen(bounded, [[intervention('consume', 'consume'), probe('read', bounded),
                                     intervention('release', 'release')]])
        _, observed = capture(pw, out, f'fresh_read_{size}', request, session_state=session_state)
        attempt = observed['steps'][0]['attempt']
        assert attempt['rc'] == 0 and attempt['fresh_read']['read_rc'] == min(size, 64)
        assert bytes.fromhex(attempt['fresh_read']['content_hex']) == payload[:64]
        assert bounded.read_bytes() == payload
    read_observations = {'before': before['fresh_read'], 'during': during['fresh_read'],
                         'after': after['fresh_read'], 'release_result': release['native_result']}
    (out / 'access-observations.json').write_text(json.dumps(read_observations, indent=2) + '\n')

    placements = {
        'delivered_only': [[probe('read', target)]],
        'consume_only': [[intervention('consume', 'consume'), probe('read', target)], [probe('later', target)]],
        'same_phase': [[probe('before', target), intervention('consume', 'consume'), probe('during', target),
                        intervention('release', 'release'), probe('after', target)]],
        'later_consume': [[probe('before', target)], [intervention('consume', 'consume'), probe('during', target)],
                          [intervention('release', 'release'), probe('after', target)]],
        'intervention_only_phases': [[intervention('consume', 'consume')], [probe('during', target)],
                                     [intervention('release', 'release')], [probe('after', target)]],
    }
    for name, phases in placements.items():
        request = specimen(target, phases)
        _, reply = capture(pw, out, name, request, session_state=session_state)
        declared = [(p['phase_id'], a['step_id'], a['extension']['operation']) for p in request['phases']
                    for a in p['actions'] if 'extension' in a]
        events = reply.get('extension_events', [])
        assert [(e['phase_id'], e['step_id'], e['operation']) for e in events] == declared
        assert reply['extensions'][0]['issuance_status'] == 'issued'
        assert reply['extensions'][0]['delivery_status'] == 'delivered'
        assert all(e['status'] == 'returned' and e['result_published'] for e in events)
        if events:
            assert events[0]['native_result'] != -1
        if len(events) == 2:
            assert events[1]['native_result'] == 0
        assert all(p['completion_observed'] for p in reply['phases'])
        assert reply['runner_subprocess']['reaped']
        for step in reply['steps']:
            if step['step_id'] in ('during', 'later') or name == 'consume_only':
                assert bytes.fromhex(step['attempt']['fresh_read']['content_hex']) == contents
        if name == 'intervention_only_phases':
            assert all(reply['phases'][i]['collection_status'] == 'not_needed' for i in (0, 2))

    ordinary = specimen(target, [[probe('ordinary', target)]])
    ordinary.pop('extensions')
    _, reply = capture(pw, out, 'no_declaration', ordinary, session_state=session_state)
    assert not reply.get('extensions') and not reply.get('extension_events')

    unavailable = specimen(target, [[intervention('consume', 'consume'), probe('read', target),
                                     intervention('release', 'release')]])
    absent_issuer = str(target_dir / 'absent-issuer')
    unavailable['_test_overrides'] = {'issuer_executable_path': absent_issuer}
    _, reply = capture(pw, out, 'issuer_capability', unavailable, expected_rc=1, session_state=session_state)
    assert reply['normalized_outcome'] == 'bad_request'
    assert reply['request_failure'] == {'code': 'extension_issuer_unavailable', 'path': ['extensions']}
    assert reply['extensions'][0]['issuance_status'] == 'issuer_unavailable'
    assert not reply.get('runner_subprocess') and not reply.get('extension_events')
    assert reply['test_overrides']['issuer_executable_path'] == absent_issuer
    assert target.read_bytes() == contents

    missing = target_dir / 'absent-target'
    failed = specimen(missing, [[intervention('consume', 'consume')],
                               [probe('absent', missing), intervention('release', 'release')]])
    _, reply = capture(pw, out, 'preparation_failure', failed, session_state=session_state)
    declaration, = reply['extensions']
    assert declaration['preparation_status'] == 'resolution_failed'
    assert declaration['preparation_errno'] != 0 and not declaration.get('issuer')
    assert declaration['issuance_status'] == 'not_started'
    assert [e['unavailable_reason'] for e in reply['extension_events']] == ['token_unavailable', 'handle_unavailable']
    assert reply['steps'][0]['sandbox_check']['outcome'] == 'prediction_unavailable'
    assert reply['steps'][0]['comparison']['order'] == 'unestablished'
    assert not missing.exists()

    alias = target_dir / 'target-symlink'
    alias.symlink_to(target)
    linked = specimen(alias, [[intervention('consume', 'consume'), probe('linked', alias), intervention('release', 'release')]])
    _, reply = capture(pw, out, 'symlink', linked, session_state=session_state)
    declaration, = reply['extensions']
    assert declaration['submitted_target'] == str(alias) and declaration['resolved_target'] == str(target.resolve())
    assert declaration['identity']['inode'] == metadata.st_ino
    assert bytes.fromhex(reply['steps'][0]['attempt']['fresh_read']['content_hex']) == contents
    assert alias.is_symlink() and target.read_bytes() == contents

    # Issuance preparation describes the original identity. Ordinary worker
    # actions replace it before consumption; later fresh observations must not
    # borrow the issuance identity or assert target stability.
    replacement = target_dir / 'replaced-target'
    replacement.write_bytes(b'original before replacement')
    original = replacement.stat()
    held = os.open(replacement, os.O_RDONLY)  # Outside worker inheritance (CLOEXEC).
    try:
        remove, create = probe('remove', replacement), probe('create', replacement)
        for value, operation, action in ((remove, 'file-write-unlink', 'unlink'), (create, 'file-write-data', 'create')):
            value['sandbox_check']['operation'] = operation
            value['attempt']['action'] = action
        changed = specimen(replacement, [[remove, create, intervention('consume', 'consume')],
                                          [probe('replacement_read', replacement), intervention('release', 'release')]])
        _, reply = capture(pw, out, 'replacement', changed, session_state=session_state)
        observed = replacement.stat()
        assert observed.st_ino != original.st_ino and replacement.read_bytes() == b''
        assert reply['extensions'][0]['identity']['inode'] == original.st_ino
        assert all(s['attempt']['rc'] == 0 for s in reply['steps'][:2])
        fresh = reply['steps'][2]['attempt']['fresh_read']
        if fresh['open_rc'] >= 0:
            assert fresh['identity']['inode'] == observed.st_ino and fresh['read_rc'] == 0
        (out / 'replacement-observations.json').write_text(json.dumps({'original_inode': original.st_ino,
            'replacement_inode': observed.st_ino, 'original_fd_cloexec': not os.get_inheritable(held),
            'replacement_length': observed.st_size, 'fresh_read': fresh}, indent=2) + '\n')
    finally:
        os.close(held)
    print('Native lifecycle, optional/same/cross-phase placement, preparation, symlink and replacement observations passed.')


def main():
    pw, directory, *state = sys.argv[1:]
    session_state = json.loads(Path(state[0]).read_text()) if state else None
    run_suite(pw, Path(directory).resolve(), session_state)


if __name__ == '__main__':
    main()

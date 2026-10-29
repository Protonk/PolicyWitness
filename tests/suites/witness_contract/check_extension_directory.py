"""Public directory extensions: independent effects beside native observations."""
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import consumer
from contract import REQUEST_SCHEMA
from lifecycle_oracle import check_record
from run_capture import RunCapture
from worker_exit_witness import worker_exit_witness

CONTENTS = b'PW directory contents before the attempt\n'
POLICY = ('(version 1)(allow default)(deny file-read-data)(deny file-write*)'
          '(allow file-read-data (extension "com.apple.app-sandbox.read")'
          '(extension "com.apple.app-sandbox.read-write"))'
          '(allow file-write* (extension "com.apple.app-sandbox.read-write"))')
NO_PREDICATE = '(version 1)(allow default)(deny file-read-data)(deny file-write*)'
CASES = ('read_write', 'no_consume', 'no_predicate', 'different_directory', 'read_only', 'default_read')


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def observe(path):
    result = dict(path=str(path))
    try:
        info = path.lstat()
    except FileNotFoundError:
        return dict(result, exists=False, errno=2)
    result.update(exists=True, regular=stat.S_ISREG(info.st_mode), size=info.st_size,
                  identity=dict(device=info.st_dev, inode=info.st_ino, mode=info.st_mode,
                                uid=info.st_uid, gid=info.st_gid))
    if result['regular']:
        result['content_hex'] = path.read_bytes().hex()
    return result


def probe(identity, action, target):
    return dict(step_id=identity, sandbox_check=dict(operation='file-read-data' if action == 'read_fresh' else 'file-write-data',
                filter=dict(kind='path', value=str(target))),
                attempt=dict(kind='file', action=action, target=str(target)))


def event(operation):
    fields = dict(operation=operation, handle_ref='handle')
    if operation == 'consume':
        fields['token_ref'] = 'token'
    return dict(step_id=operation, extension=fields)


def actions(target, boundary):
    return [probe(boundary + '-read', 'read_fresh', target / (boundary + '-existing')),
            probe(boundary + '-write', 'write_fresh', target / (boundary + '-existing')),
            probe(boundary + '-create', 'create_fresh', target / (boundary + '-child'))]


def native_content(write, *, create):
    """Expected bytes from the recorded calls; checked against external bytes."""
    if write['open_rc'] == -1:
        return None if create else CONTENTS
    if not create and write['truncate_rc'] != 0:
        return CONTENTS
    return b'x' if write['write_rc'] == 1 else b''


def assert_external(record, content):
    if content is None:
        assert record.get('exists') is False and record['errno'] == 2, record
    else:
        assert record.get('regular') is True and record['size'] == len(content), record
        assert record['content_hex'] == content.hex(), record


def execute(pw, out, root, ownership, name, request, paths, session, *, expected_rc=0):
    folder = out / name
    if session:
        request['runner'] = dict(mode='byoxpc', service=session['service_name'])
    entry = dict(case=name, capture=str(folder), worker_exit_witnessed=False, witness='not launched')
    ownership['attempts'].append(entry)
    save(root / 'ownership.json', ownership); save(out / 'ownership.json', ownership)
    envelope = None
    try:
        with RunCapture(pw, folder, request, cli_args=['--timeout-ms', '20000']) as capture:
            rc = capture.wait(timeout=40)
            # Inspect effects before looking at the producer's interpretation.
            effects = [observe(path) for path in paths]
            save(folder / 'external-final.json', effects)
            envelope = capture.load_json()
    finally:
        # Also preserve effects on native, transport or assertion failure, before
        # owned targets can be cleaned. Missing reap leaves durable staging.
        folder.mkdir(parents=True, exist_ok=True)
        effects = [observe(path) for path in paths]
        save(folder / 'external-final.json', effects)
        entry['worker_exit_witnessed'], entry['witness'] = worker_exit_witness(envelope)
        save(root / 'ownership.json', ownership); save(out / 'ownership.json', ownership)
    assert rc == expected_rc, (name, rc, folder / 'capture.json')
    errors = consumer.validate(envelope)
    assert not errors, (name, errors)
    errors = check_record(envelope)
    assert not errors, (name, errors)
    assert entry['worker_exit_witnessed'], entry
    return envelope, {value['path']: value for value in effects}


def run(pw, out, session=None):
    out.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='pw-extension-directory-', dir='/private/tmp'))
    ownership = dict(staging=str(root), artifacts=str(out), attempts=[], removed=False)
    save(root / 'ownership.json', ownership); save(out / 'ownership.json', ownership)
    summary = []
    try:
        for case in CASES:
            target, other = root / case, root / (case + '-other')
            target.mkdir(mode=0o700); other.mkdir(mode=0o700)
            boundaries = ('before', 'during', 'after')
            paths = [target / (boundary + '-' + kind) for boundary in boundaries for kind in ('existing', 'child')]
            for path in paths[::2]:
                path.write_bytes(CONTENTS); path.chmod(0o600)
            baseline = dict(schema_version=REQUEST_SCHEMA, specimen_id='directory-baseline-' + case,
                            policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'),
                            probe_plan=[action for boundary in boundaries for action in actions(target, boundary)])
            envelope, final = execute(pw, out, root, ownership, case + '-baseline', baseline, paths, session)
            for path in paths:
                assert_external(final[str(path)], b'x')
            assert all(step['attempt']['rc'] == 0 for step in envelope['data']['runner_result']['steps'])
            # Restore the same controlled existing files; remove baseline children.
            # No baseline descriptor or child is available to the issued token.
            for path in paths[::2]: path.write_bytes(CONTENTS)
            for path in paths[1::2]: path.unlink()
            before = {str(path): observe(path) for path in paths}
            assert all(before[str(path)]['exists'] is False for path in paths[1::2])
            declaration = dict(token_ref='token', target=str(other if case == 'different_directory' else target))
            if case != 'default_read':
                declaration['authority'] = 'read' if case == 'read_only' else 'read_write'
            phases = [dict(phase_id='before', actions=actions(target, 'before'))]
            if case != 'no_consume': phases.append(dict(phase_id='consume', actions=[event('consume')]))
            phases.append(dict(phase_id='during', actions=actions(target, 'during')))
            if case != 'no_consume': phases.append(dict(phase_id='release', actions=[event('release')]))
            phases.append(dict(phase_id='after', actions=actions(target, 'after')))
            request = dict(schema_version=REQUEST_SCHEMA, specimen_id='directory-' + case,
                           policy=dict(format='sbpl', sbpl_source=NO_PREDICATE if case == 'no_predicate' else POLICY),
                           extensions=[declaration], phases=phases)
            (out / case).mkdir()
            save(out / case / 'before-issuance.json', dict(target=observe(target), other=observe(other), files=before,
                 basis='owned paths observed before launch; issuance precedes worker actions; no other writer'))
            envelope, final = execute(pw, out, root, ownership, case, request, paths, session)
            runner = envelope['data']['runner_result']
            assert runner['normalized_outcome'] == 'ok' and runner['sandboxed_after_apply']
            issued, = runner['extensions']
            assert issued['extension_class'] == ('com.apple.app-sandbox.read' if case in ('read_only', 'default_read') else 'com.apple.app-sandbox.read-write')
            assert issued['issuance_status'] == 'issued' and issued['delivery_status'] == 'delivered'
            assert issued['resolved_target'] == declaration['target']
            assert issued['issuer']['euid'] == os.geteuid() and issued['issuer']['uid'] == os.getuid()
            assert issued['issuer']['pid'] != runner['runner_subprocess']['pid']
            events = runner.get('extension_events') or []
            if case == 'no_consume':
                assert events == []
            else:
                assert [item['operation'] for item in events] == ['consume', 'release']
                assert all(item['status'] == 'returned' and item['result_published'] for item in events)
                assert events[0]['native_result'] != -1
                assert type(events[1]['native_result']) is int  # No required revocation/result pattern.
            observed = {step['step_id']: step for step in runner['steps']}
            for boundary in boundaries:
                read = observed[boundary + '-read']['attempt']
                positive_read = boundary == 'during' and case in ('read_write', 'read_only', 'default_read')
                if positive_read:
                    assert read['rc'] == 0 and read['fresh_read']['content_hex'] == CONTENTS.hex()
                elif boundary != 'after' or case not in ('read_write', 'read_only', 'default_read'):
                    assert read['fresh_read']['open_rc'] == -1
                for action, create in (('write', False), ('create', True)):
                    step = observed[boundary + '-' + action]
                    attempt, native = step['attempt'], step['attempt']['fresh_write']
                    path = target / (boundary + ('-child' if create else '-existing'))
                    assert_external(final[str(path)], native_content(native, create=create))
                    if create:
                        assert native['preopen_stat']['rc'] == -1 and native['preopen_stat']['errno'] == 2
                        assert step['sandbox_check']['outcome'] == 'prediction_unavailable'
                        assert step['comparison']['order'] == 'unestablished'
                        assert 'query_plan:path_unresolved_at_planning' in step['comparison']['limitations']
                    else:
                        assert step['comparison']['order'] == 'query_first'
                        assert final[str(path)]['identity']['inode'] == before[str(path)]['identity']['inode']
                    if boundary == 'during' and case == 'read_write':
                        assert attempt['rc'] == 0 and native['open_rc'] >= 0
                        assert native['write_rc'] == 1 and native['close_rc'] == 0
                        assert native['opened_stat']['size'] == (0 if create else len(CONTENTS))
                        assert native['written_stat']['size'] == 1
                        if not create:
                            assert native['truncate_rc'] == 0 and native['truncated_stat']['size'] == 0
                        assert_external(final[str(path)], b'x')
                    elif boundary == 'before' or case != 'read_write':
                        assert native['open_rc'] == -1 and attempt['errno'] in (1, 13)
                        assert_external(final[str(path)], None if create else CONTENTS)
            assert list(other.iterdir()) == []
            assert all(phase['arrival_observed'] and phase['completion_observed'] for phase in runner['phases'])
            summary.append(dict(case=case, extension_class=issued['extension_class'],
                native_events=events, after_release_and_exit=final,
                fresh_after_release=[observed['after-' + action]['attempt'] for action in ('read', 'write', 'create')]))
            save(out / 'observations.json', summary)
            print(case + ': independent modification, creation and persistence observations passed', flush=True)

        # Preserve the distinction between a native effect and an unpublished
        # attempt: the existing seam kills only after the new helper returned.
        target = root / 'unpublished'; target.write_bytes(CONTENTS)
        request = dict(schema_version=REQUEST_SCHEMA, specimen_id='directory-unpublished',
            policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'),
            probe_plan=[probe('write', 'write_fresh', target), probe('after', 'read_fresh', target)],
            _test_overrides=dict(worker_kill_before_publish_slot=0))
        envelope, final = execute(pw, out, root, ownership, 'unpublished', request, [target], session, expected_rc=1)
        assert_external(final[str(target)], b'x')
        runner = envelope['data']['runner_result']
        assert runner['runner_subprocess']['reaped'] and runner['runner_subprocess']['term_signal'] == 9
        for step, expected_summary in zip(runner['steps'], ('started_without_result', 'not_reached')):
            attempt = step['attempt']
            assert attempt['outcome'] == 'no_completed_result' and attempt['result_source'] == 'synthetic'
            assert attempt.get('fresh_write') is None and attempt.get('fresh_read') is None
            assert attempt['lifecycle']['summary'] == expected_summary
        print('unpublished: independent write effect retained; unpublished native fields withheld', flush=True)
    finally:
        cleanup_safe = all(entry['worker_exit_witnessed'] for entry in ownership['attempts'])
        if cleanup_safe:
            shutil.rmtree(root); ownership['removed'] = True
        else:
            ownership['recovery'] = 'Confirm each unwitnessed worker exit before removing this exact owned staging directory.'
            save(root / 'ownership.json', ownership)
        save(out / 'cleanup.json', ownership)
        if not cleanup_safe:
            raise AssertionError('directory staging retained after unknown worker cleanup: ' + str(root))


if __name__ == '__main__':
    pw, output, *state = sys.argv[1:]
    run(pw, Path(output).resolve(), json.loads(Path(state[0]).read_text()) if state else None)

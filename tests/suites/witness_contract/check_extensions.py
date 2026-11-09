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
import build_context
from witness_capture import capture


def probe(identity, target):
    return {'step_id': identity, 'sandbox_check': {'operation': 'file-read-data',
            'filter': {'kind': 'path', 'value': str(target)}},
            'attempt': {'kind': 'file', 'action': 'read_fresh', 'target': str(target)}}


def intervention(identity, operation):
    value = {'operation': operation, 'handle_ref': 'handle'}
    if operation == 'consume':
        value['delivery_ref'] = 'delivery'
    return {'step_id': identity, 'extension': value}


def specimen(target, phases, *, authority='read', policy=None, terminate_issuer=False):
    policy = policy or '(version 1)(allow default)(deny file-read-data)(allow file-read-data (extension "com.apple.app-sandbox.read"))'
    subject = [{'phase_id': f'p{i}', 'actor_id': 'subject', 'actions': actions} for i, actions in enumerate(phases)]
    issuance = {'phase_id':'issuer_final','actor_id':'issuer','actions':[
        {'step_id':'issue','extension':{'operation':'issue','family':'file','authority':authority,'target':str(target),'token_ref':'token'}},
        {'step_id':'transfer','extension':{'operation':'transfer','token_ref':'token','recipient':'subject','delivery_ref':'delivery'}}]}
    # Keep a baseline before issuing where the submitted phase is genuinely a baseline.
    insertion = 1 if subject and not any('extension' in a for a in subject[0]['actions']) and any(
        a.get('extension',{}).get('operation')=='consume' for p in subject[1:] for a in p['actions']) else 0
    ordered = subject[:insertion] + [issuance] + subject[insertion:]
    if terminate_issuer:
        dependent=next(p for p in ordered if any(a.get('extension',{}).get('operation')=='consume' for a in p['actions']))
        dependent['after_termination']={'actor_id':'issuer'}
    return {'contract':build_context.candidate_contract(),'specimen_id':'extensions',
        'actors':[{'actor_id':'issuer','equipment':'unentitled','sandbox':{'mode':'unapplied'}},
                  {'actor_id':'subject','equipment':'selected','sandbox':{'mode':'apply','policy':{'format':'sbpl','sbpl_source':policy}}}],
        'phases':ordered}


def lifecycle_events(runner):
    return [e for e in runner['extension_events'] if e['operation'] in ('consume','release')]


def assert_issuance(runner):
    issue=next(e for e in runner['extension_events'] if e['operation']=='issue')
    assert issue['status']=='returned' and issue['native_nonnull'] is True and issue['result_published'] and issue['call_boundary_observed'],issue
    transfer=runner['transfers'][0]
    assert transfer['status']=='delivered' and transfer['equality']=='equal' and transfer['recipient_acknowledged'] and transfer['source_acknowledged'],transfer
    actors={a['actor_id']:a for a in runner['actors']}
    assert len({a['launch']['pid'] for a in actors.values()})==len(actors)
    assert all(a['subprocess']['reaped'] for a in actors.values())
    return issue


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
    spec = specimen(target, [[probe('before', target)], [intervention('consume', 'consume')],
                             [probe('during', target), intervention('release', 'release')],
                             [probe('after', target)]], terminate_issuer=True)
    envelope, runner = capture(pw, out, 'lifecycle', spec, session_state=session_state)
    assert runner['normalized_outcome'] == 'finished', runner
    assert envelope['result']['normalized_outcome'] == 'finished' and envelope['result']['ok'] is True, envelope['result']
    issue=assert_issuance(runner)
    assert issue['target']==str(target)
    actors={a['actor_id']:a for a in runner['actors']}
    assert actors['subject']['applied'] and actors['subject']['application_count']==1
    gate=next(p['termination_gate'] for p in runner['phases'] if p.get('termination_gate'))
    assert gate['outcome']=='satisfied' and gate['activation_eligible']
    reap=actors['issuer']['owned_reap']
    activation=next(p['activation_observation'] for p in runner['phases'] if p['phase_id']=='issuer_final')
    assert gate['observation']['capture_ordinal']==reap['capture_ordinal']
    assert activation['capture_ordinal']<reap['capture_ordinal']<gate['capture_ordinal']
    assert reap['observed_ns']>=activation['observed_ns']
    assert reap['native_rc']==actors['issuer']['launch']['pid']
    assert reap['ownership_unbroken'] and not reap['departure_requested']
    consume, release = lifecycle_events(runner)
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
    assert request['contract'] == 'BUILD_CONTRACT'
    request['contract'] = build_context.candidate_contract()
    _, documented = capture(pw, out, 'guide_example', request, session_state=session_state)
    assert_issuance(documented)
    consumed, released = lifecycle_events(documented)
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
        assert_issuance(reply)
        assert all(e['status'] == ('delivered' if e['operation']=='transfer' else 'returned') and e['result_published'] for e in events)
        lifecycle=lifecycle_events(reply)
        if lifecycle: assert lifecycle[0]['native_result'] != -1
        if len(lifecycle)==2: assert lifecycle[1]['native_result'] == 0
        assert all(p['completion_observed'] for p in reply['phases'])
        assert all(a['subprocess']['reaped'] for a in reply['actors'])
        for step in reply['steps']:
            if step['step_id'] in ('during', 'later') or name == 'consume_only':
                assert bytes.fromhex(step['attempt']['fresh_read']['content_hex']) == contents
        if name == 'intervention_only_phases':
            assert all(p['collection_status']=='not_needed' for p in reply['phases'] if p['phase_id'] in ('p0','p2','issuer_final'))

    ordinary={'contract':build_context.candidate_contract(),'specimen_id':'ordinary_without_authority',
              'policy':{'format':'sbpl','sbpl_source':'(version 1)(allow default)'},
              'probe_plan':[probe('ordinary',target)]}
    _, reply=capture(pw,out,'ordinary_without_authority',ordinary,session_state=session_state)
    assert not reply.get('actors') and not reply.get('extension_events') and not reply.get('authority_setup')
    assert reply['runner_subprocess']['reaped']
    assert bytes.fromhex(reply['steps'][0]['attempt']['fresh_read']['content_hex'])==contents

    missing = target_dir / 'absent-target'
    failed = specimen(missing, [[intervention('consume', 'consume')],
                               [probe('absent', missing), intervention('release', 'release')]])
    _, reply = capture(pw, out, 'preparation_failure', failed, session_state=session_state)
    issue=next(e for e in reply['extension_events'] if e['operation']=='issue')
    assert issue['target']==str(missing) and issue['call_boundary_observed'] and issue['result_published']
    assert reply['steps'][0]['attempt']['rc'] != 0
    # Missing targets reach native issuance unchanged; no host-resolution result is invented.
    assert 'extensions' not in reply
    assert not missing.exists()

    alias = target_dir / 'target-symlink'
    alias.symlink_to(target)
    linked = specimen(alias, [[intervention('consume', 'consume'), probe('linked', alias), intervention('release', 'release')]])
    _, reply = capture(pw, out, 'symlink', linked, session_state=session_state)
    issue=assert_issuance(reply)
    assert issue['target']==str(alias)
    assert reply['steps'][0]['attempt']['fresh_read']['identity']['inode']==metadata.st_ino
    assert bytes.fromhex(reply['steps'][0]['attempt']['fresh_read']['content_hex']) == contents
    assert alias.is_symlink() and target.read_bytes() == contents

    # The independent original identity precedes issuance. Ordinary actor
    # actions replace it before consumption; later fresh observations must
    # identify their own opened object, without asserting target stability.
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
        assert next(e for e in reply['extension_events'] if e['operation']=='issue')['target']==str(replacement)
        assert all(s['attempt']['rc'] == 0 for s in reply['steps'][:2])
        fresh = reply['steps'][2]['attempt']['fresh_read']
        if fresh['open_rc'] >= 0:
            assert fresh['identity']['inode'] == observed.st_ino and fresh['read_rc'] == 0
        (out / 'replacement-observations.json').write_text(json.dumps({'original_inode': original.st_ino,
            'replacement_inode': observed.st_ino, 'original_fd_cloexec': not os.get_inheritable(held),
            'replacement_length': observed.st_size, 'fresh_read': fresh}, indent=2) + '\n')
    finally:
        os.close(held)
    print('Actor lifecycle, natural-termination ordering, optional/same/cross-phase placement, submitted paths and replacement observations passed.')


def main():
    pw, directory, *state = sys.argv[1:]
    session_state = json.loads(Path(state[0]).read_text()) if state else None
    run_suite(pw, Path(directory).resolve(), session_state)


if __name__ == '__main__':
    main()

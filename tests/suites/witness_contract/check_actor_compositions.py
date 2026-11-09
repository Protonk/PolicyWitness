"""Public composition controls with distinct resources and exact action ownership.

This case requires the positive read-extension path on its equipment. A native
refusal stays in the raw capture and fails positive coverage; it is never
reported as a kernel contract violation or silently accepted as coverage.
"""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
from witness_capture import capture
import build_context
from consumer import validate
from lifecycle_oracle import check_record
from worker_exit_witness import worker_exit_witness
import extension_actors as actors


def specimen(x, y):
    def phase(name, actor, actions):
        return dict(phase_id=name, actor_id=actor, actions=actions)
    return dict(contract=build_context.candidate_contract(), specimen_id='actor_compositions', actors=[
        actors.unapplied_actor('A'), actors.unapplied_actor('D'),
        actors.apply_actor('B', actors.C_POLICY), actors.apply_actor('C', actors.C_POLICY)], phases=[
        phase('supply_x', 'A', [actors.issue('issue_x', 'tx', x),
            actors.transfer('x_to_b', 'tx', 'B', 'dbx'), actors.transfer('x_to_c', 'tx', 'C', 'dcx'),
            actors.transfer('x_to_a', 'tx', 'A', 'dax')]),
        # The next global action is B's first local slot, not A's next slot.
        phase('a_empty', 'A', []),
        phase('b_before', 'B', [actors.read_probe('b_x_before', x), actors.read_probe('b_y_before', y)]),
        phase('c_before', 'C', [actors.read_probe('c_x_before', x), actors.read_probe('c_y_before', y)]),
        phase('supply_y', 'D', [actors.issue('issue_y', 'ty', y), actors.transfer('y_to_b', 'ty', 'B', 'dby')]),
        phase('b_x', 'B', [actors.consume('b_x_first', 'dbx', 'hbx1'),
            actors.read_probe('b_x_after', x), actors.read_probe('b_y_before_consume', y),
            actors.consume('b_x_again', 'dbx', 'hbx2'), actors.release('b_release_x1', 'hbx1'),
            actors.read_probe('b_x_after_one_release', x)]),
        phase('c_x', 'C', [actors.consume('c_x_consume', 'dcx', 'hcx'),
            actors.read_probe('c_x_after', x), actors.read_probe('c_y_without_delivery', y),
            actors.release('c_release_x', 'hcx')]),
        phase('b_y', 'B', [actors.consume('b_y_consume', 'dby', 'hby'), actors.read_probe('b_y_after', y),
            actors.release('b_release_y', 'hby'), actors.release('b_release_x2', 'hbx2')]),
        phase('a_self', 'A', [actors.consume('a_self_consume', 'dax', 'hax'), actors.release('a_release_x', 'hax')]),
        phase('d_empty', 'D', [])])


def renamed(original):
    spec = copy.deepcopy(original)
    actor_names = {'A': 'sender-x', 'D': 'sender-y', 'B': 'recipient-two', 'C': 'recipient-one'}
    spec['specimen_id'] = 'actor_compositions_renamed'
    spec['actors'].reverse()
    for actor in spec['actors']:
        actor['actor_id'] = actor_names[actor['actor_id']]
    for phase in spec['phases']:
        phase['actor_id'] = actor_names[phase['actor_id']]
        phase['phase_id'] = 'renamed_' + phase['phase_id']
        for action in phase['actions']:
            action['step_id'] = 'renamed_' + action['step_id']
            op = action.get('extension')
            if op:
                for key in ('token_ref', 'delivery_ref', 'handle_ref'):
                    if key in op:
                        op[key] = 'renamed_' + op[key]
                if 'recipient' in op:
                    op['recipient'] = actor_names[op['recipient']]
    return spec


def request_captures(spec):
    for actor in spec['actors']:
        if actor['sandbox']['mode'] == 'apply':
            actor['sandbox']['policy'].update(capture_compiled_profile=True, capture_nonce=os.urandom(16).hex())


def assert_composition(envelope, runner, spec, resources, prefix, failed_actor=None):
    assert validate(envelope, build_context.candidate_contract()) == [], validate(envelope, build_context.candidate_contract())
    assert check_record(envelope, build_context.candidate_contract()) == [], check_record(envelope, build_context.candidate_contract())
    assert worker_exit_witness(envelope)[0], worker_exit_witness(envelope)
    assert runner['normalized_outcome'] == ('runner_failed' if failed_actor else 'finished'), runner.get('error')
    got_actors = {a['actor_id']: a for a in runner['actors']}
    assert len(got_actors) == len(spec['actors']) == 4
    pids = {a['actor_id']: a['launch']['pid'] for a in runner['actors']}
    assert len(set(pids.values())) == 4
    for expected in spec['actors']:
        actual = got_actors[expected['actor_id']]
        assert actual['mode'] == expected['sandbox']['mode']
        equipment=actual['equipment']
        assert equipment['requested']==expected['equipment'] and equipment['resolved']==expected['equipment']
        assert equipment['requirements_status']=='satisfied'
        if expected['actor_id']==failed_actor:
            assert equipment['execution']['status']=='unobserved' and equipment['execution']['reason']=='setup_unavailable'
        else:
            assert equipment['execution']['status']=='matched' and equipment['execution']['eligible']
            assert equipment['execution']['pid']==actual['launch']['pid']
        assert actual['subprocess']['reaped'] is True and actual['subprocess']['exit_code'] == 0
        assert actual['subprocess']['pid'] == actual['launch']['pid']
        assert actual['launch']['parent_pid'] == runner['pid']
        if expected['sandbox']['mode'] == 'apply':
            digest = hashlib.sha256(expected['sandbox']['policy']['sbpl_source'].encode()).hexdigest()
            assert actual['policy_sha256'] == actual['policy_received_sha256'] == digest
            if expected['actor_id'] == failed_actor:
                assert actual['setup_status'] == 'setup_failed' and actual['applied'] is False and actual['application_count'] == 0
            else:
                assert actual['setup_status'] == 'applied' and actual['applied'] is True and actual['application_count'] == 1
                assert actual['application']=={'state':'observed','basis':'applied_publication'}
        else:
            assert actual['setup_status'] == 'unapplied_declared' and actual['application_count'] == 0
            assert actual['application']=={'state':'not_requested','basis':'unapplied_declaration'}
        policy = expected['sandbox'].get('policy', {})
        capture = actual.get('compiled_profile')
        if policy.get('capture_compiled_profile'):
            assert 'schema_version' not in capture
            assert capture['worker_pid'] == pids[expected['actor_id']]
            if expected['actor_id'] == failed_actor:
                assert capture['status'] == 'unavailable' and capture.get('bytecode_b64') is None
                assert capture.get('producer') is None and capture.get('capture_stage') is None
                assert capture.get('reason') and capture.get('request_nonce') is None
            else:
                assert capture['status'] == 'captured'
                assert capture['request_nonce'] == policy['capture_nonce']
                assert capture['producer'] == 'worker' and capture['capture_stage'] == 'before_apply'
                bytecode = base64.b64decode(capture['bytecode_b64'], validate=True)
                assert len(bytecode) == capture['bytecode_length'] > 0
                assert hashlib.sha256(bytecode).hexdigest() == capture['bytecode_sha256']
                assert capture['source_sha256'] == hashlib.sha256(policy['sbpl_source'].encode()).hexdigest()
                assert capture['source_length'] == len(policy['sbpl_source'].encode())
                assert capture['parameter_count'] == 0
                assert capture['params_sha256'] == hashlib.sha256(bytes(4)).hexdigest()
        else:
            assert capture is None
    expected_actions = [(phase, action) for phase in spec['phases'] for action in phase['actions']]
    expected_steps = [a['step_id'] for _, a in expected_actions if 'attempt' in a]
    expected_events = [a['step_id'] for _, a in expected_actions if 'extension' in a]
    assert [s['step_id'] for s in runner['steps']] == expected_steps
    assert [e['step_id'] for e in runner['extension_events']] == expected_events
    assert [p['phase_id'] for p in runner['phases']] == [p['phase_id'] for p in spec['phases']]
    for expected, actual in zip(spec['phases'], runner['phases']):
        assert actual['actor_id'] == expected['actor_id']
        assert actual['action_ids'] == [a['step_id'] for a in expected['actions']]
        if expected['actor_id'] == failed_actor:
            assert not actual['arrival_observed'] and not actual['completion_observed']
        else:
            assert actual['arrival_observed'] and actual['completion_observed']
        assert actual['ordering']['protocol_violations'] == []
    steps = {s['step_id']: s for s in runner['steps']}
    events = {e['step_id']: e for e in runner['extension_events']}
    for phase, action in expected_actions:
        actual = events[action['step_id']] if 'extension' in action else steps[action['step_id']]
        assert actual['actor_id'] == phase['actor_id'] and actual['phase_id'] == phase['phase_id']
        if phase['actor_id'] == failed_actor:
            if 'extension' in action:
                assert actual['result_published'] is False and actual['call_boundary_observed'] is False
                assert actual.get('native_result') is None
            else:
                assert actual['attempt']['rc'] != 0 and actual['comparison']['order'] != 'query_first'
            continue
        if 'extension' in action:
            op = action['extension']
            assert actual['operation'] == op['operation'] and actual['result_published'] is True
            for key in ('token_ref', 'delivery_ref', 'handle_ref'):
                if key in op:
                    assert actual[key] == op[key]
            if op['operation'] != 'transfer':
                assert actual['status'] == 'returned' and actual['call_boundary_observed'] is True, (action, actual)
            if op['operation'] == 'issue':
                assert actual['native_nonnull'] is True, ('positive issuance coverage missing', actual)
                assert actual['target'] == op['target'] and actual['flags'] == 0
                assert actual['extension_class'] == 'com.apple.app-sandbox.read'
            if op['operation'] == 'consume':
                assert actual['native_result'] != -1, ('positive consumption coverage missing', actual)
        else:
            assert actual['attempt']['result_source'] == 'worker'
            assert actual['comparison']['order'] == 'query_first'
            assert actual['sandbox_check']['pid'] == pids[phase['actor_id']]
    expected_tokens = {a['extension']['token_ref']: (p['actor_id'], a) for p, a in expected_actions
                       if a.get('extension', {}).get('operation') == 'issue'}
    tokens = {t['token_ref']: t for t in runner['resources']['tokens']}
    assert set(tokens) == set(expected_tokens)
    for ref, (owner, action) in expected_tokens.items():
        assert tokens[ref]['actor_id'] == owner and tokens[ref]['step_id'] == action['step_id']
        assert tokens[ref]['status'] == 'issued'
    expected_transfers = {a['extension']['delivery_ref']: (p['actor_id'], a) for p, a in expected_actions
                          if a.get('extension', {}).get('operation') == 'transfer'}
    deliveries = {d['delivery_ref']: d for d in runner['resources']['deliveries']}
    transfers = {t['delivery_ref']: t for t in runner['transfers']}
    assert set(deliveries) == set(transfers) == set(expected_transfers)
    for ref, (owner, action) in expected_transfers.items():
        op = action['extension']
        for actual in (deliveries[ref], transfers[ref]):
            assert actual['source_actor_id'] == owner and actual['recipient_actor_id'] == op['recipient']
            assert actual['token_ref'] == op['token_ref'] and actual['step_id'] == action['step_id']
            assert actual['status'] == ('recipient_unavailable' if op['recipient'] == failed_actor else 'delivered')
        if op['recipient'] == failed_actor:
            assert transfers[ref]['copy_status'] == 'not_copied' and transfers[ref]['recipient_acknowledged'] is False
        else:
            assert transfers[ref]['equality'] == 'equal' and transfers[ref]['recipient_acknowledged'] is True
        assert transfers[ref]['source_acknowledged'] is True
    handles = {h['handle_ref']: h for h in runner['resources']['handles']}
    consumes = [(p, a) for p, a in expected_actions if a.get('extension', {}).get('operation') == 'consume']
    assert set(handles) == {a['extension']['handle_ref'] for _, a in consumes}
    for phase, action in consumes:
        op = action['extension']; actual = handles[op['handle_ref']]
        assert actual['actor_id'] == phase['actor_id'] and actual['delivery_ref'] == op['delivery_ref']
        assert actual['step_id'] == action['step_id']
        assert actual.get('native_handle') == events[action['step_id']].get('native_result')
    denied = ('b_x_before', 'b_y_before', 'c_x_before', 'c_y_before', 'b_y_before_consume', 'c_y_without_delivery')
    for name in denied:
        if failed_actor and name.startswith('c_'):
            continue
        attempt = steps[prefix + name]['attempt']
        assert attempt['rc'] != 0 and attempt['fresh_read']['open_rc'] < 0, (name, attempt)
    for name, resource in [('b_x_after', 'x'), ('c_x_after', 'x'), ('b_y_after', 'y')]:
        if failed_actor and name.startswith('c_'):
            continue
        attempt = steps[prefix + name]['attempt']; fresh = attempt['fresh_read']; target = resources[resource]
        assert attempt['rc'] == 0 and fresh['open_rc'] >= 0, ('positive fresh-access coverage missing', name, attempt)
        assert bytes.fromhex(fresh['content_hex']) == target['contents']
        assert fresh['identity']['device'] == target['device'] and fresh['identity']['inode'] == target['inode']
    # The additional read after releasing one of two handles is retained but
    # does not assume a native handle-refcount or revocation rule.
    return dict(pids=pids, action_count=len(expected_actions),
                after_one_release=steps[prefix + 'b_x_after_one_release']['attempt'],
                native_releases={e['step_id']: e.get('native_result') for e in events.values() if e['operation'] == 'release'})


def main(pw, out):
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    directory = Path(tempfile.mkdtemp(prefix='pw-compositions-', dir='/private/tmp'))
    ownership = dict(directory=str(directory), artifacts=str(out.resolve()),
                     run_id=os.environ.get('PW_TEST_RUN_ID'), state='running', reaped_captures=[])
    def receipt():
        encoded = json.dumps(ownership, indent=2) + '\n'
        (out / 'ownership.json').write_text(encoded)
        (directory / 'ownership.json').write_text(encoded)
    receipt()
    try:
        resources = {}
        for key, contents in [('x', b'PW distinct resource X\n'), ('y', b'PW other resource Y\n')]:
            path = Path(directory) / key; path.write_bytes(contents); metadata = path.stat()
            resources[key] = dict(path=path, contents=contents, device=metadata.st_dev, inode=metadata.st_ino)
        base = specimen(resources['x']['path'], resources['y']['path'])
        failed = copy.deepcopy(base)
        failed['specimen_id'] = 'actor_compositions_failed_recipient'
        next(a for a in failed['actors'] if a['actor_id'] == 'C')['sandbox']['policy']['sbpl_source'] = '(version 1) (allow'
        request_captures(failed)
        captured = copy.deepcopy(base)
        captured['specimen_id'] = 'actor_compositions_captured'
        request_captures(captured)
        for name, request, prefix, failed_actor in [('original', base, '', None),
                ('renamed', renamed(base), 'renamed_', None), ('failed_recipient', failed, '', 'C'),
                ('captured', captured, '', None)]:
            envelope, runner = capture(pw, out, name, request, expected_rc=1 if failed_actor else 0)
            assert worker_exit_witness(envelope)[0], worker_exit_witness(envelope)
            ownership['reaped_captures'].append(name)
            receipt()
            report[name] = assert_composition(envelope, runner, request, resources, prefix, failed_actor)
            if name == 'captured':
                # Keep the actual capture and change only its claimed producer;
                # actor-local context must be checked as strictly as top-level capture.
                changed = copy.deepcopy(envelope)
                next(a for a in changed['data']['runner_result']['actors']
                     if a['actor_id'] == 'B')['compiled_profile']['producer'] = 'host'
                errors = validate(changed, build_context.candidate_contract())
                assert 'B: compiled_profile requires worker/before_apply context' in errors, errors
                (out / 'capture-context-control.json').write_text(json.dumps(dict(
                    mutation='actor B compiled_profile.producer = host', errors=errors), indent=2) + '\n')
        for target in resources.values():
            assert target['path'].read_bytes() == target['contents']
    except BaseException:
        ownership['state'] = 'retained_after_failure'
        receipt()
        raise
    ownership['state'] = 'host_reaped_all_actors'
    receipt()
    shutil.rmtree(directory)  # Exactly this fixture's new directory, after witnessed exits.
    ownership['state'] = 'removed_after_host_reap'
    (out / 'ownership.json').write_text(json.dumps(ownership, indent=2) + '\n')
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('four public compositions preserve resource associations, independent progress after recipient failure and per-actor compiled-profile receipts')


if __name__ == '__main__':
    main(sys.argv[1], Path(sys.argv[2]))

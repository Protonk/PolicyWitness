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


def gate_specimen(target, unavailable_dependent):
    spec = dict(contract=build_context.candidate_contract(),
        specimen_id='gate_unreached' if unavailable_dependent else 'gate_cancels_schedule',
        actors=[actors.apply_actor(name, actors.CALIBRATION_POLICY)
                for name in ('source', 'dependent', 'unrelated')], phases=[
            dict(phase_id='source_final', actor_id='source', actions=[]),
            dict(phase_id='dependent', actor_id='dependent',
                 after_termination=dict(actor_id='source'),
                 actions=[actors.read_probe('dependent_read', target)]),
            dict(phase_id='unrelated', actor_id='unrelated',
                 actions=[actors.read_probe('unrelated_read', target)])])
    if unavailable_dependent:
        spec['actors'][1]['sandbox']['policy']['sbpl_source'] = '(version 1) (allow'
    else:
        # The existing seam sleeps after the worker's final phase, before done.
        # Only source reaches that sleep: the other actors remain unactivated.
        # Keep normal host allowances so an overall deadline cannot stand in
        # for the failed gate's cancellation of later unrelated work.
        spec['_test_overrides'] = dict(worker_post_apply_hang_ms=10000)
    return spec


def assert_unactivated(phase, step):
    assert phase.get('activation_observation') is None and phase.get('visit_timing') is None
    assert phase['arrival_observed'] is False and phase['completion_observed'] is False
    assert phase['collection_status'] == 'not_reached' and phase.get('validator_subprocess') is None
    ordering = phase['ordering']
    assert ordering['collection_closed_before_proceed'] is False
    assert ordering['proceed_set'] is False and ordering['proceed_observed'] is False
    assert ordering['validator_disposition'] == 'not_invoked' and ordering['protocol_violations'] == []
    attempt = step['attempt']
    assert attempt['result_source'] == 'synthetic' and attempt['missing_reason'] == 'slot_incomplete'
    assert attempt['outcome'] == 'no_completed_result' and attempt.get('fresh_read') is None
    lifecycle = attempt['lifecycle']
    assert lifecycle['summary'] == 'not_reached'
    assert lifecycle['boundary']['state'] == 'supported' and lifecycle['boundary']['answer'] == 'not_reached'
    assert lifecycle['result']['state'] == 'supported' and lifecycle['result']['answer'] == 'unpublished'
    assert step['sandbox_check']['result_source'] == 'synthetic'
    assert step['sandbox_check']['missing_reason'] == 'validator_not_invoked'
    assert step['comparison']['order'] == 'unestablished'


def assert_gate_schedule(runner, spec, target, unavailable_dependent):
    assert runner['normalized_outcome'] == 'runner_failed'
    assert [actor['actor_id'] for actor in runner['actors']] == ['source', 'dependent', 'unrelated']
    assert [phase['phase_id'] for phase in runner['phases']] == ['source_final', 'dependent', 'unrelated']
    assert [step['step_id'] for step in runner['steps']] == ['dependent_read', 'unrelated_read']
    actor_records = {actor['actor_id']: actor for actor in runner['actors']}
    pids = [actor['launch']['pid'] for actor in runner['actors']]
    assert len(set(pids)) == 3 and all(pid > 0 for pid in pids)
    for expected, actual in zip(spec['actors'], runner['actors']):
        failed = unavailable_dependent and expected['actor_id'] == 'dependent'
        assert actual['setup_status'] == ('setup_failed' if failed else 'applied')
        assert actual['applied'] is (not failed) and actual['application_count'] == (0 if failed else 1)
        digest = hashlib.sha256(expected['sandbox']['policy']['sbpl_source'].encode()).hexdigest()
        assert actual['policy_sha256'] == actual['policy_received_sha256'] == digest
        assert actual['launch']['parent_pid'] == runner['pid']
        sub = actual['subprocess']
        assert sub['pid'] == actual['launch']['pid'] and sub['reaped'] is True
        # Final collection remains observable for each launched actor, including
        # both parked actors after cancellation and the setup failure neighbour.
        assert sub['collection_basis'] == 'after_confirmed_reap'
        assert isinstance(sub.get('worker_evidence'), dict) and isinstance(sub.get('disposition'), dict)
        reap = actual['owned_reap']
        assert reap['pid'] == reap['native_rc'] == sub['pid'] and reap['ownership_unbroken'] is True
    source, dependent, unrelated = runner['phases']
    assert source['arrival_observed'] is True and source['completion_observed'] is True
    assert source['collection_status'] == 'not_needed'
    assert source['ordering']['collection_closed_before_proceed'] is True
    assert source['ordering']['proceed_set'] is True and source['ordering']['proceed_observed'] is True
    assert source['ordering']['protocol_violations'] == []
    assert unrelated.get('termination_gate') is None
    assert_unactivated(dependent, runner['steps'][0])
    gate = dependent['termination_gate']
    assert gate['source_actor_id'] == 'source' and gate['source_final_phase_id'] == 'source_final'
    assert gate['activation_eligible'] is False
    execution = runner['schedule']['execution_wait']
    assert execution['clock_fault'] is False and execution['elapsed_ms'] < execution['budget_ms']
    if unavailable_dependent:
        assert gate['outcome'] == 'not_reached'
        assert all(gate.get(name) is None for name in ('wait', 'observation', 'capture_ordinal'))
        assert runner['schedule'].get('cancelled') is None and execution['stop'] == 'schedule_complete'
        assert unrelated['activation_observation']['capture_ordinal'] > 0
        assert unrelated['arrival_observed'] is True and unrelated['completion_observed'] is True
        assert unrelated['collection_status'] == 'collected' and unrelated['validator_subprocess']['reaped'] is True
        ordering = unrelated['ordering']
        assert ordering['collection_closed_before_proceed'] is True
        assert ordering['proceed_set'] is True and ordering['proceed_observed'] is True
        assert ordering['protocol_violations'] == []
        step = runner['steps'][1]
        assert step['sandbox_check']['result_source'] == 'validator'
        assert step['sandbox_check']['pid'] == actor_records['unrelated']['launch']['pid']
        assert step['comparison']['order'] == 'query_first'
        attempt = step['attempt']
        assert attempt['result_source'] == 'worker' and attempt['rc'] == 0
        fresh = attempt['fresh_read']
        assert fresh['open_rc'] >= 0 and bytes.fromhex(fresh['content_hex']) == target['contents']
        assert fresh['identity']['device'] == target['device'] and fresh['identity']['inode'] == target['inode']
    else:
        assert gate['outcome'] == 'timed_out' and gate.get('observation') is None
        assert gate['wait']['budget_ms'] == 5000 and gate['wait']['stop'] == 'timed_out'
        assert gate['wait']['clock_fault'] is False
        assert runner['schedule']['cancelled'] == 'termination_dependency:timed_out'
        assert execution['stop'] == 'dependency_failed'
        assert source['activation_observation']['capture_ordinal'] < gate['capture_ordinal']
        assert actor_records['source']['owned_reap']['capture_ordinal'] > gate['capture_ordinal']
        assert actor_records['source']['subprocess']['exit_requested'] is True
        assert_unactivated(unrelated, runner['steps'][1])
    return dict(gate=gate, schedule=runner['schedule'],
                phases=runner['phases'], attempts=runner['steps'],
                final_collection={name: actor['subprocess'] for name, actor in actor_records.items()})



def timeout_applicability_specimens(target):
    # The ordinary sentinel starts after readiness and excludes collection.
    # Actor execution keeps its separate allowance. The same post-phase sleep
    # is shorter than the separate final cleanup grace in both forms.
    overrides = dict(worker_timeout_ms=200, worker_post_apply_hang_ms=500)
    ordinary = dict(contract=build_context.candidate_contract(),
        specimen_id='ordinary_worker_timeout',
        policy=dict(format='sbpl', sbpl_source=actors.CALIBRATION_POLICY),
        probe_plan=[], _test_overrides=dict(overrides))
    actor = dict(contract=build_context.candidate_contract(),
        specimen_id='actor_ignores_worker_timeout',
        actors=[actors.apply_actor(name, actors.CALIBRATION_POLICY) for name in ('source', 'reader')],
        phases=[dict(phase_id='source_final', actor_id='source', actions=[]),
            dict(phase_id='read_after_source', actor_id='reader',
                after_termination=dict(actor_id='source'),
                actions=[actors.read_probe('read_after_source', target)])],
        _test_overrides=dict(overrides))
    return [('ordinary_worker_timeout', ordinary, False), ('actor_ignores_worker_timeout', actor, True)]


def assert_timeout_applicability(runner, spec, target, actor_form):
    assert runner['specimen_id'] == spec['specimen_id']
    assert runner['test_overrides'] == spec['_test_overrides']
    assert runner.get('request_failure') is None
    if not actor_form:
        assert runner['normalized_outcome'] == 'runner_timeout' and runner['rc'] == 1
        assert runner['sandboxed_after_apply'] is True
        assert runner['steps'] == [] and len(runner['phases']) == 1
        phase = runner['phases'][0]
        assert phase['phase_id'] == 'main' and phase['action_ids'] == []
        assert phase['arrival_observed'] is True and phase['completion_observed'] is True
        assert phase['collection_status'] == 'not_needed' and phase.get('validator_subprocess') is None
        assert phase['ordering']['proceed_observed'] is True
        sub = runner['runner_subprocess']
        assert sub['pid'] == runner['pid'] and sub['pid'] > 0 and sub['reaped'] is True
        assert sub['ready_byte_received'] is True and sub['collection_basis'] == 'after_confirmed_reap'
        assert sub['done_observed'] is True and sub['exit_code'] == 0 and sub.get('term_signal') is None
        assert sub.get('termination_request') is None and sub['grace_end'] == 'reaped_during_grace'
        assert sub['poll_stop_reason'] == 'sentinel_deadline' and sub['partial_steps'] is False
        wait = sub['sentinel_wait']
        assert wait['budget_ms'] == 200 and wait['stop'] == 'sentinel_deadline' and wait['clock_fault'] is False
        assert type(wait['elapsed_ms']) is int and type(wait['excluded_ms']) is int
        assert wait['elapsed_ms'] - wait['excluded_ms'] >= 200
        # Final done and a natural exit in grace establish that the worker
        # passed its post-phase seam; they do not rewrite the earlier timeout.
        return dict(sentinel_wait=wait, subprocess=sub, phase=phase)
    assert runner['execution_form'] == 'actors'
    assert runner['normalized_outcome'] == 'finished' and runner['rc'] == 0
    assert [a['actor_id'] for a in runner['actors']] == ['source', 'reader']
    assert [p['phase_id'] for p in runner['phases']] == ['source_final', 'read_after_source']
    assert [s['step_id'] for s in runner['steps']] == ['read_after_source']
    source_actor, reader_actor = runner['actors']
    assert source_actor['launch']['pid'] != reader_actor['launch']['pid']
    digest = hashlib.sha256(actors.CALIBRATION_POLICY.encode()).hexdigest()
    for actual in runner['actors']:
        assert actual['setup_status'] == 'applied' and actual['applied'] is True and actual['application_count'] == 1
        assert actual['application'] == dict(state='observed', basis='applied_publication')
        assert actual['policy_sha256'] == actual['policy_received_sha256'] == digest
        assert actual['launch']['parent_pid'] == runner['pid']
        sub = actual['subprocess']
        assert sub['pid'] == actual['launch']['pid'] and sub['pid'] > 0
        assert sub['reaped'] is True and sub['exit_code'] == 0 and sub.get('term_signal') is None
        assert sub['ready_byte_received'] is True and sub['done_observed'] is True
        assert sub['collection_basis'] == 'after_confirmed_reap' and sub.get('sentinel_wait') is None
        assert sub.get('termination_request') is None
    schedule = runner['schedule']
    assert schedule.get('cancelled') is None and schedule['setup_wait']['budget_ms'] == 10000
    execution = schedule['execution_wait']
    assert execution['budget_ms'] == 120000 and execution['stop'] == 'schedule_complete'
    assert execution['clock_fault'] is False
    assert type(execution['elapsed_ms']) is int and type(execution['excluded_ms']) is int
    charged_ms = execution['elapsed_ms'] - execution['excluded_ms']
    assert 200 < charged_ms < 120000, execution
    source_phase, reader_phase = runner['phases']
    assert source_phase['action_ids'] == [] and reader_phase['action_ids'] == ['read_after_source']
    for phase in runner['phases']:
        assert phase['arrival_observed'] is True and phase['completion_observed'] is True
        assert phase['ordering']['collection_closed_before_proceed'] is True
        assert phase['ordering']['proceed_set'] is True and phase['ordering']['proceed_observed'] is True
        assert phase['ordering']['protocol_violations'] == []
    assert source_phase['collection_status'] == 'not_needed'
    assert reader_phase['collection_status'] == 'collected' and reader_phase['validator_subprocess']['reaped'] is True
    gate, reap = reader_phase['termination_gate'], source_actor['owned_reap']
    assert gate['outcome'] == 'satisfied' and gate['activation_eligible'] is True
    assert gate['source_actor_id'] == 'source' and gate['source_final_phase_id'] == 'source_final'
    assert gate['wait']['budget_ms'] == 5000 and gate['wait']['stop'] == 'satisfied'
    assert gate['wait']['clock_fault'] is False
    assert gate['observation'] == dict(capture_ordinal=reap['capture_ordinal'])
    assert reap['pid'] == reap['native_rc'] == source_actor['launch']['pid']
    assert reap['ownership_unbroken'] is True and reap['departure_requested'] is False and reap['raw_status'] == 0
    assert source_phase['activation_observation']['capture_ordinal'] < reap['capture_ordinal'] < gate['capture_ordinal']
    # Source ordinals share one child sequence. Reader ordinals are separate;
    # their clock observations, not their ordinals, establish this time order.
    assert source_phase['activation_observation']['observed_ns'] <= reap['observed_ns'] <= reader_phase['activation_observation']['observed_ns']
    step = runner['steps'][0]
    assert step['phase_id'] == 'read_after_source' and step['actor_id'] == 'reader'
    assert step['sandbox_check']['result_source'] == 'validator'
    assert step['sandbox_check']['pid'] == reader_actor['launch']['pid']
    assert step['comparison']['order'] == 'query_first'
    attempt = step['attempt']
    assert attempt['result_source'] == 'worker' and attempt['outcome'] == 'ok' and attempt['rc'] == 0
    assert attempt['requested_kind'] == 'file' and attempt['requested_action'] == 'read_fresh'
    assert attempt['requested_path'] == str(target['path'])
    fresh = attempt['fresh_read']
    assert fresh['open_rc'] >= 0 and fresh['stat_rc'] == 0 and fresh['close_rc'] == 0
    assert fresh['read_rc'] == len(target['contents']) and bytes.fromhex(fresh['content_hex']) == target['contents']
    identity = (target['device'], target['inode'])
    assert (fresh['identity']['device'], fresh['identity']['inode']) == identity
    after = target['path'].stat()
    assert (after.st_dev, after.st_ino) == identity and target['path'].read_bytes() == target['contents']
    return dict(schedule=schedule, charged_execution_ms=charged_ms, gate=gate,
        source_reap=reap, reader_subprocess=reader_actor['subprocess'], fresh_read=fresh,
        independent_file=dict(path=str(target['path']), content_hex=target['contents'].hex(),
                              device=identity[0], inode=identity[1]))

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
        for name, unavailable in [('gate_cancels_schedule', False), ('gate_unreached', True)]:
            request = gate_specimen(resources['x']['path'], unavailable)
            envelope, runner = capture(pw, out, name, request, expected_rc=1)
            assert worker_exit_witness(envelope)[0], worker_exit_witness(envelope)
            ownership['reaped_captures'].append(name)
            receipt()
            report[name] = assert_gate_schedule(runner, request, resources['x'], unavailable)
        for name, request, actor_form in timeout_applicability_specimens(resources['x']['path']):
            envelope, runner = capture(pw, out, name, request, expected_rc=0 if actor_form else 1)
            assert worker_exit_witness(envelope)[0], worker_exit_witness(envelope)
            ownership['reaped_captures'].append(name)
            receipt()
            report[name] = assert_timeout_applicability(runner, request, resources['x'], actor_form)
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
    print('public compositions preserve resources, profiles and gate scope; ordinary worker timeout leaves actor scheduling allowances intact')


if __name__ == '__main__':
    main(sys.argv[1], Path(sys.argv[2]))

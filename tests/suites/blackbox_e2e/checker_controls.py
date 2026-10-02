#!/usr/bin/env python3
"""Exercise the checker CLI with independently specified evidence and faults.

Every control here is authored against the current contract: the consumer's
version gate, the uniform data skeleton, the D1 comparison record, the
ordering chain and the reporting-failure rules. Baselines are retained live
envelopes (`tests/fixtures/blackbox_e2e/checker`); nothing is derived from
the checker or the production code under test.
"""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests/fixtures/blackbox_e2e"
CHECKER = Path(__file__).with_name("validate_run.py")
sys.path.insert(0, str(ROOT / 'tests/lib'))
import contract
from blackbox import envelope_skeleton
from consumer import denials, lifecycle, select, steps, validate
from path_diagnostics_contract import check_cases
from worker_exit_witness import worker_exit_witness


def consumer_controls(artifacts, current):
    """Constructed JSON interpretation controls against a retained live envelope."""
    records = []

    def run(name, envelope, expected=None, rejected_by=None):
        path = artifacts / ('consumer_' + name + '.json')
        path.write_text(json.dumps(envelope, indent=2) + '\n')
        errors = validate(envelope)
        (artifacts / ('consumer_' + name + '.errors.json')).write_text(json.dumps(errors, indent=2) + '\n')
        if rejected_by is None:
            assert not errors, (name, errors)
            if expected is not None:
                expected(envelope)
            records.append({'control': name, 'rejected': False})
        else:
            assert any(rejected_by in error for error in errors), (name, rejected_by, errors)
            records.append({'control': name, 'rejected': True, 'errors': errors})

    def runner(envelope):
        return envelope['data']['runner_result']

    def first(envelope):
        return runner(envelope)['steps'][0]

    def require(condition, reason):
        assert condition, reason

    # The retained live run validates and its first row is read by field.
    def allowed_write(e):
        chosen = select(steps(e), step_id='fs_write_allowed', observation='succeeded', order='query_first')
        require(len(chosen) == 1 and chosen[0]['attempt']['outcome'] == 'ok', 'allowed write must be selectable by its record')
    run('retained_live_run', current, allowed_write)

    # Attempt forms have their own compact contract beside the query forms.
    resolved = copy.deepcopy(current)
    attempt = first(resolved)['attempt']
    attempt['requested_path'] = '/link/file'
    attempt['path_diagnostics'] = dict(input='/link/file', observer='runner_host',
        phase='after_orchestration', same_as_input=[], realpath_resolved='/real/file',
        parent_realpath_resolved=None)
    # The query names the same target so the record's target relation holds.
    first(resolved)['sandbox_check']['filter_value'] = '/link/file'
    first(resolved)['sandbox_check']['path_diagnostics']['input'] = '/link/file'
    for record in runner(resolved)['validator_subprocess']['records']:
        if record['step_id'] == 'fs_write_allowed':
            record['filter_value'] = '/link/file'
    run('attempt_path_forms', resolved)
    for name, change, diagnostic in [
        ('input_mismatch', lambda a: a['path_diagnostics'].update(input='/unrelated/file'), 'input differs from requested_path'),
        ('wrong_observer', lambda a: a['path_diagnostics'].update(observer='worker'), 'host/phase provenance'),
        ('wrong_phase', lambda a: a['path_diagnostics'].update(phase='before_attempt'), 'host/phase provenance'),
        ('missing_compact', lambda a: a['path_diagnostics'].pop('same_as_input'), 'require same_as_input'),
        ('duplicate_form', lambda a: a['path_diagnostics'].update(same_as_input=['realpath_resolved']*2), 'unique supported form names'),
        ('missing_form', lambda a: a['path_diagnostics'].pop('parent_realpath_resolved'), 'exclusively'),
        ('missing_forms', lambda a: a.pop('path_diagnostics'), 'without path diagnostics'),
    ]:
        malformed = copy.deepcopy(resolved)
        change(first(malformed)['attempt'])
        run('attempt_path_' + name, malformed, rejected_by=diagnostic)

    # Removed keys are rejected at their exact path; none is reconstructed.
    removed = [
        ('step_drift', lambda e: first(e).update(drift=False), 'removed key steps[].drift'),
        ('step_deny_signal', lambda e: first(e).update(deny_signal=None), 'removed key steps[].deny_signal'),
        ('comparison_prediction', lambda e: first(e)['comparison'].update(prediction='allow'), 'removed key comparison.prediction'),
        ('comparison_conclusion', lambda e: first(e)['comparison'].update(conclusion='agreement'), 'removed key comparison.conclusion'),
        ('comparison_scope', lambda e: first(e)['comparison'].update(scope='submitted_operation_and_target'), 'removed key comparison.scope'),
        ('comparison_obligations', lambda e: first(e)['comparison'].update(obligations=[]), 'removed key comparison.obligations'),
        ('comparison_references', lambda e: first(e)['comparison'].update(references=[]), 'removed key comparison.references'),
        ('attempt_exit_code', lambda e: first(e)['attempt'].update(exit_code=0), 'removed key attempt.exit_code'),
        ('attempt_syscall_errno', lambda e: first(e)['attempt'].update(syscall_errno=None), 'removed key attempt.syscall_errno'),
        ('attempt_native_rc', lambda e: first(e)['attempt'].update(native_rc=0), 'removed key attempt.native_rc'),
        ('query_scope', lambda e: first(e)['sandbox_check'].update(scope='post_sandbox'), 'removed key sandbox_check.scope'),
        ('query_effective_filter_value', lambda e: first(e)['sandbox_check'].update(effective_filter_value='/x'), 'removed key sandbox_check.effective_filter_value'),
        ('reply_deny_signal_total', lambda e: runner(e).update(deny_signal_total=None), 'removed key deny_signal_total'),
        ('reply_comparison_conditions', lambda e: runner(e).update(comparison_conditions={}), 'removed key comparison_conditions'),
        ('data_runner_startup_diagnostics', lambda e: e['data'].update(runner_startup_diagnostics=None), 'removed key data.runner_startup_diagnostics'),
        ('data_policy_augmentation', lambda e: e['data'].update(policy_augmentation=None), 'removed key data.policy_augmentation'),
        ('data_request_path', lambda e: e['data'].update(request_path='/x'), 'removed key data.request_path'),
        ('data_error', lambda e: e['data'].update(error='x'), 'removed key data.error'),
        ('diagnostics_worker_pid', lambda e: e['data']['runner_sandbox_diagnostics'].update(worker_pid=1), 'removed key data.runner_sandbox_diagnostics.worker_pid'),
        ('diagnostics_capture_status', lambda e: e['data']['runner_sandbox_diagnostics'].update(capture_status='disabled'), 'removed key data.runner_sandbox_diagnostics.capture_status'),
        ('diagnostics_first_deny', lambda e: e['data']['runner_sandbox_diagnostics'].update(first_deny=None), 'removed key data.runner_sandbox_diagnostics.first_deny'),
    ]
    for name, change, diagnostic in removed:
        broken = copy.deepcopy(current)
        change(broken)
        run('removed_' + name, broken, rejected_by=diagnostic)

    # Vocabulary and classification against the raw channel fields.
    for name, change, diagnostic in [
        ('foreign_limitation', lambda e: first(e)['comparison']['limitations'].append('sandbox_attribution_unestablished'), 'outside the vocabulary'),
        ('repeated_limitation', lambda e: first(e)['comparison'].update(limitations=['attempt:not_reached'] * 2), 'repeated limitation'),
        ('lifecycle_limitation_on_completed', lambda e: first(e)['comparison'].update(limitations=['attempt:not_reached']), 'lifecycle limitations'),
        ('plan_limitation_without_exclusion', lambda e: first(e)['comparison'].update(limitations=['query_plan:unrecognized_filter_kind']), 'without a planning exclusion'),
        ('observation_disagrees', lambda e: first(e)['comparison'].update(observation='permission_failure', observation_basis='permission_errno'), 'disagrees with the attempt fields'),
        ('basis_disagrees', lambda e: first(e)['comparison'].update(observation_basis='spawned_child'), 'disagrees with the attempt fields'),
        ('operation_relation_disagrees', lambda e: first(e)['comparison'].update(operation_relation='different'), 'disagrees with the submitted operations'),
        ('target_relation_disagrees', lambda e: first(e)['comparison'].update(target_relation='different_submitted'), 'disagrees with the submitted targets'),
        ('unknown_observation', lambda e: first(e)['comparison'].update(observation='agreement'), 'invalid comparison.observation'),
        ('unknown_order', lambda e: first(e)['comparison'].update(order='future_order'), 'invalid comparison.order'),
        ('missing_comparison', lambda e: first(e).pop('comparison'), 'missing comparison'),
        ('missing_query', lambda e: first(e).pop('sandbox_check'), 'missing sandbox_check'),
        ('missing_attempt', lambda e: first(e).pop('attempt'), 'missing attempt'),
    ]:
        broken = copy.deepcopy(current)
        change(broken)
        run('classification_' + name, broken, rejected_by=diagnostic)

    # The ordering chain: query_first needs the complete chain and an eligible
    # native record; an eligible record with the chain must say query_first.
    def ordering(e):
        return runner(e)['runner_subprocess']['ordering']
    for name, change, diagnostic in [
        ('collection_not_closed', lambda e: ordering(e).update(collection_closed_before_proceed=False), 'lacks eligible record or ordering chain'),
        ('proceed_not_set', lambda e: ordering(e).update(proceed_set=False), 'lacks eligible record or ordering chain'),
        ('proceed_not_observed', lambda e: ordering(e).update(proceed_observed=False), 'lacks eligible record or ordering chain'),
        ('lifetime_unestablished', lambda e: ordering(e).update(worker_lifetime_established=False), 'lacks eligible record or ordering chain'),
        ('failed_apply', lambda e: runner(e).update(sandboxed_after_apply=False), 'lacks eligible record or ordering chain'),
        ('missing_ordering', lambda e: runner(e)['runner_subprocess'].pop('ordering'), 'ordering is required'),
        ('synthetic_query', lambda e: first(e)['sandbox_check'].update(result_source='synthetic'), 'lacks eligible record or ordering chain'),
        ('incoherent_native', lambda e: first(e)['sandbox_check'].update(native_rc=1), 'lacks eligible record or ordering chain'),
        ('wrong_pid', lambda e: first(e)['sandbox_check'].update(pid=runner(e)['runner_subprocess']['pid'] + 1), 'lacks eligible record or ordering chain'),
        ('wrong_tuple', lambda e: runner(e)['validator_subprocess']['records'][0].update(filter_value='/other'), 'lacks eligible record or ordering chain'),
        ('duplicate_record', lambda e: runner(e)['validator_subprocess']['records'].append(copy.deepcopy(runner(e)['validator_subprocess']['records'][0])), 'lacks eligible record or ordering chain'),
        ('unestablished_despite_chain', lambda e: first(e)['comparison'].update(order='unestablished'), 'requires query_first'),
    ]:
        broken = copy.deepcopy(current)
        change(broken)
        run('order_' + name, broken, rejected_by=diagnostic)
    # A recorded violation beside a falsified chain flag is not a contradiction
    # the validator invents: the fault must be listed.
    broken = copy.deepcopy(current)
    ordering(broken).update(proceed_set=False)
    for step in runner(broken)['steps']:
        step['comparison']['order'] = 'unestablished'
    run('order_unmarked_violation', broken, rejected_by='unmarked ordering protocol violation')
    # The marked fault is retained beside the raw chain; no row claims an order.
    ordering(broken)['protocol_violations'] = ['acknowledgement_without_release']
    run('order_marked_violation_retained', broken)

    # Reporting failures retain diagnostic observations but certify no comparison.
    def degraded(e, retained=True):
        r = runner(e)
        r.update(rc=1, normalized_outcome='runner_reporting_failed', error='host invariant rejected',
                 reporting_failure=dict(origin='runner_host', diagnostic='missing ordering', original_rc=0,
                                        original_normalized_outcome='ok', original_error=None, evidence_retained=retained))
        e['result'].update(ok=False, exit_code=1, normalized_outcome='runner_reporting_failed')
        for step in r['steps']:
            step['comparison'] = None
        if not retained:
            r['steps'] = []
            r.pop('runner_subprocess', None)
            r.pop('validator_subprocess', None)
    def preserved(e):
        view = lifecycle(e)
        require(view['reporting'] == 'reported', 'retained lifecycle evidence must remain readable')
        require(all(s['comparison'] is None for s in steps(e)), 'every comparison withheld')
    failed = copy.deepcopy(current)
    degraded(failed)
    run('reporting_failure_preserved', failed, preserved)
    minimal = copy.deepcopy(current)
    degraded(minimal, retained=False)
    run('reporting_failure_minimal', minimal, lambda e: require(steps(e) == [], 'no steps without retention'))
    for name, change, diagnostic in [
        ('comparison_kept', lambda e: first(e).update(comparison=copy.deepcopy(first(current)['comparison'])), 'must withhold every comparison'),
        ('ok_summary', lambda e: runner(e).update(normalized_outcome='ok'), 'reporting failure requires a failed summary'),
        ('rc_zero', lambda e: runner(e).update(rc=0), 'reporting failure requires a failed summary'),
        ('missing_marker', lambda e: runner(e).pop('reporting_failure'), 'invalid reporting_failure diagnostics'),
        ('bad_marker', lambda e: runner(e).update(reporting_failure='invalid'), 'invalid reporting_failure diagnostics'),
        ('false_retention', lambda e: runner(e)['reporting_failure'].update(evidence_retained=False), 'without evidence retention must omit'),
    ]:
        broken = copy.deepcopy(failed)
        change(broken)
        run('reporting_failure_' + name, broken, rejected_by=diagnostic)
    for key in ['origin', 'diagnostic', 'original_rc', 'original_normalized_outcome', 'evidence_retained']:
        broken = copy.deepcopy(failed)
        runner(broken)['reporting_failure'].pop(key)
        run('reporting_failure_missing_' + key, broken, rejected_by='invalid reporting_failure diagnostics')

    # The host's raw launch evidence is preserved without an errno allowlist.
    spawn = dict(origin='runner_host', operation='posix_spawn',
                 executable_path='/unknown/validator-"é"', return_code=2147483647,
                 diagnostic='unfamiliar native launch diagnostic')
    spawned = copy.deepcopy(current)
    r = runner(spawned)
    r.update(rc=1, normalized_outcome='validator_spawn_failed', error='native launch failure', validator_spawn_failure=copy.deepcopy(spawn))
    spawned['result'].update(ok=False, exit_code=1, normalized_outcome='validator_spawn_failed')
    r.pop('validator_subprocess')
    r['runner_subprocess']['ordering']['validator_disposition'] = 'not_spawned'
    for step in r['steps']:
        step['sandbox_check'].update(outcome='error', result_source='synthetic', native_rc=None, errno=None,
                                     missing_reason='validator_not_invoked')
        step['comparison'].update(order='unestablished')
    run('unfamiliar_spawn_failure', spawned, lambda e: require(runner(e)['validator_spawn_failure'] == spawn, 'raw launch record changed'))
    for name, change, diagnostic in [
        ('zero_code', lambda e: runner(e)['validator_spawn_failure'].update(return_code=0), 'invalid validator_spawn_failure'),
        ('string_code', lambda e: runner(e)['validator_spawn_failure'].update(return_code='2'), 'invalid validator_spawn_failure'),
        ('missing_path', lambda e: runner(e)['validator_spawn_failure'].pop('executable_path'), 'invalid validator_spawn_failure'),
        ('foreign_origin', lambda e: runner(e)['validator_spawn_failure'].update(origin='validator'), 'invalid validator_spawn_failure'),
        ('with_subprocess', lambda e: runner(e).update(validator_subprocess=dict(reaped=True, records=[])), 'cannot coexist'),
    ]:
        broken = copy.deepcopy(spawned)
        change(broken)
        run('malformed_spawn_' + name, broken, rejected_by=diagnostic)

    # The lifecycle record is required beside a worker subprocess.
    unrecorded = copy.deepcopy(current)
    runner(unrecorded)['runner_subprocess'].pop('disposition')
    run('record_required', unrecorded, rejected_by='without runner_subprocess.disposition')

    # D5: versions are read exactly, before anything else.
    for name, change, diagnostic in [
        ('envelope_previous', lambda e: e.update(schema_version=contract.CONTROLLER_ENVELOPE - 1), 'unsupported controller envelope'),
        ('envelope_next', lambda e: e.update(schema_version=contract.CONTROLLER_ENVELOPE + 1), 'unsupported controller envelope'),
        ('envelope_string', lambda e: e.update(schema_version=str(contract.CONTROLLER_ENVELOPE)), 'malformed controller envelope'),
        ('envelope_missing', lambda e: e.pop('schema_version'), 'malformed controller envelope'),
        ('reply_previous', lambda e: runner(e).update(schema_version=contract.RESPONSE_SCHEMA - 1), 'unsupported runner response'),
        ('reply_next', lambda e: runner(e).update(schema_version=contract.RESPONSE_SCHEMA + 1), 'unsupported runner response'),
        ('reply_float', lambda e: runner(e).update(schema_version=float(contract.RESPONSE_SCHEMA)), 'malformed runner response'),
        ('reply_missing', lambda e: runner(e).pop('schema_version'), 'malformed runner response'),
    ]:
        broken = copy.deepcopy(current)
        change(broken)
        errors = validate(broken)
        assert len(errors) == 1 and diagnostic in errors[0], (name, errors)
        for reader in (steps, lifecycle, denials):
            try:
                reader(broken)
            except ValueError as exc:
                assert diagnostic in str(exc), (name, reader.__name__, exc)
            else:
                raise AssertionError(f'{name}: {reader.__name__} read an unsupported document')
        records.append({'control': 'version_' + name, 'rejected': True, 'errors': errors})
    # An envelope without a reply is read under its own version only.
    no_reply = copy.deepcopy(current)
    no_reply['data'].update(runner_result=None, runner_client=None, runner_sandbox_diagnostics=None, sandbox_log_capture=None)
    no_reply['result'].update(ok=False, exit_code=2, normalized_outcome='tool_error', error='controlled')
    run('no_reply_envelope', no_reply, lambda e: require(steps(e) == [] and denials(e)['capture_status'] == 'not_reported', 'absence must not invent evidence'))
    bare = copy.deepcopy(runner(current))
    assert not validate(bare), validate(bare)
    bare['schema_version'] = contract.RESPONSE_SCHEMA + 1
    errors = validate(bare)
    assert len(errors) == 1 and 'unsupported runner response' in errors[0], errors
    records.append({'control': 'bare_reply_versions', 'rejected': True})

    # The log channel is read in place with candidate references resolved.
    event = {'pid': runner(current)['runner_subprocess']['pid'], 'operation': 'file-write-data',
             'path': first(current)['attempt']['requested_path'], 'raw_line': 'controlled denial'}
    match = {'step_id': 'fs_write_allowed', 'operation': 'file-write-data', 'operation_source': 'submitted_attempt',
             'requested_kind': 'file', 'requested_action': 'open_write', 'path': event['path'],
             'path_sources': ['submitted_attempt.target']}
    window = {'kind': 'runner_client_span', 'started_at_unix_ms': 1000, 'ended_at_unix_ms': 2500, 'pad_seconds': 2,
              'start': '1969-12-31 23:59:59+0000', 'end': '1970-01-01 00:00:05+0000',
              'event_timestamps_available': False, 'exact_run_membership': False, 'step_ordering': False,
              'pid_reuse_protection': False}
    logged = copy.deepcopy(current)
    logged['data']['sandbox_log_capture'] = {'capture_status': 'captured', 'window': window,
        'deny_events': [event, dict(event, pid=99)], 'step_denies': [{'event_index': 0,
        'candidate_step_ids': ['fs_write_allowed'], 'association': 'candidate', 'matching_evidence': [match]}]}
    logged['data']['runner_sandbox_diagnostics'].update(correlation_status='pid_match', permission_failures_without_record=[])
    def candidate(e):
        d = denials(e)
        c = d['candidates'][0]
        require(d['events'] == [event, dict(event, pid=99)], 'unmatched raw events must survive')
        require(c['event_index'] == 0 and c['event'] == event and c['association'] == 'candidate', 'candidate reference is not unique occurrence')
        require(c['matching_evidence'] == [match], 'matching provenance must survive')
        require(d['window'] == window and d['correlation_status'] == 'pid_match', 'capture limits must survive')
    run('candidate_resolution', logged, candidate)
    for status, correlation in [('captured', 'no_match'), ('blocked', 'unavailable'),
                                ('requested_unavailable', 'unavailable'), ('disabled', 'not_attempted')]:
        absent = copy.deepcopy(logged)
        absent['data']['runner_sandbox_diagnostics'].update(correlation_status=correlation, permission_failures_without_record=None)
        absent['data']['sandbox_log_capture'] = (dict(capture_status=status, window=window,
            deny_events=[dict(event, pid=99)] if status == 'captured' else None,
            step_denies=[] if status == 'captured' else None,
            blocked_reason='controlled blockage' if status == 'blocked' else None)
            if status != 'disabled' else None)
        def availability(e, status=status, correlation=correlation):
            d = denials(e)
            require((d['capture_status'], d['correlation_status']) == (status if status != 'disabled' else 'not_reported', correlation),
                    'capture states must remain distinct')
            require(d['candidates'] == ([] if status == 'captured' else None), 'no match and no report differ')
            if status == 'blocked':
                require(d['capture']['blocked_reason'] == 'controlled blockage', 'capture detail lost')
        run('capture_' + status, absent, availability)
    (artifacts / 'consumer-controls.json').write_text(json.dumps(records, indent=2) + '\n')


def client_output_control(artifacts):
    """The shipped client's own failure reply validates under the current contract.

    A connection to a service that does not exist yields a client-synthesized
    reply; it must carry the current response version with no steps.
    """
    app = Path(os.environ.get('PW_APP_DIR') or (ROOT / 'dist/PolicyWitness.app'))
    client = app / 'Contents/MacOS/pw-runner-client'
    assert client.is_file(), f'shipped client missing: {client}'
    request = artifacts / 'client-request.json'
    request.write_text(json.dumps({'schema_version': 1, 'specimen_id': 'client-control',
                                   'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'},
                                   'probe_plan': []}) + '\n')
    result = subprocess.run([str(client), 'run', '--timeout-ms', '2000', '--request', '-',
                             'com.example.pw.no-such-service.' + os.urandom(4).hex()],
                            input=request.read_bytes(), capture_output=True, timeout=30)
    (artifacts / 'client.stdout').write_bytes(result.stdout)
    (artifacts / 'client.stderr').write_bytes(result.stderr)
    assert result.returncode == 1, result
    reply = json.loads(result.stdout)
    assert reply['schema_version'] == contract.RESPONSE_SCHEMA, reply.get('schema_version')
    assert reply['normalized_outcome'] in ('xpc_error', 'xpc_timeout', 'xpc_no_reply'), reply
    assert reply['steps'] == [] and reply.get('runner_subprocess') is None, reply
    errors = validate(reply)
    assert not errors, errors
    assert not validate(envelope_skeleton(reply, ok=False)), validate(envelope_skeleton(reply, ok=False))
    print('client failure reply validates under the current contract: ' + reply['normalized_outcome'], flush=True)


def cleanup_witness_controls(artifacts):
    """Envelope shapes and the staging removal each permits; constructed, no process launched.

    Only a confirmed reap witnesses worker exit. A client-synthesized xpc_timeout
    reply, a lost reply and the minimal reporting-failure reply carry no
    subprocess record although a worker may have spawned; an unreaped or
    unrecorded reap says it may still run. Each must retain staging.
    """
    cases = [
        ('client_timeout', {'data': {'runner_result': {'normalized_outcome': 'xpc_timeout', 'steps': []}}}, False),
        ('lost_runner_reply', {'data': {'runner_result': None}}, False),
        ('no_envelope', None, False),
        ('minimal_reporting_failure', {'data': {'runner_result': {
            'normalized_outcome': 'runner_reporting_failed', 'steps': [],
            'reporting_failure': {'evidence_retained': False}}}}, False),
        ('unreaped_worker', {'data': {'runner_result': {'runner_subprocess': {'pid': 42, 'reaped': False}}}}, False),
        ('reap_unrecorded', {'data': {'runner_result': {'runner_subprocess': {'pid': 42}}}}, False),
        ('missing_pid', {'data': {'runner_result': {'runner_subprocess': {'reaped': True}}}}, False),
        ('invalid_pid', {'data': {'runner_result': {'runner_subprocess': {'pid': 0, 'reaped': True}}}}, False),
        ('negative_pid', {'data': {'runner_result': {'runner_subprocess': {'pid': -1, 'reaped': True}}}}, False),
        ('boolean_pid', {'data': {'runner_result': {'runner_subprocess': {'pid': True, 'reaped': True}}}}, False),
        ('string_pid', {'data': {'runner_result': {'runner_subprocess': {'pid': '42', 'reaped': True}}}}, False),
        ('numeric_reaped', {'data': {'runner_result': {'runner_subprocess': {'pid': 42, 'reaped': 1}}}}, False),
        ('reaped_worker', {'data': {'runner_result': {'runner_subprocess': {'pid': 42, 'reaped': True}}}}, True),
    ]
    records = []
    for name, envelope, expected in cases:
        witnessed, reason = worker_exit_witness(envelope)
        assert witnessed is expected, f'{name}: staging removal permitted={witnessed}, expected {expected}: {reason}'
        assert reason, name
        records.append({'control': name, 'removal_permitted': witnessed, 'witness': reason})
    (artifacts / 'cleanup-witness-controls.json').write_text(json.dumps(records, indent=2) + '\n')
    print('cleanup witness controls: ok', flush=True)


def mutation_order_controls(artifacts, current):
    """Unordered and ordered unlink rows: the attempt record and `order` are what the row says."""
    records = []
    base = copy.deepcopy(current)
    r = base['data']['runner_result']
    step = r['steps'][0]
    target = step['attempt']['requested_path']
    step['sandbox_check'].update(operation='file-write-unlink')
    step['attempt'].update(requested_action='unlink', outcome='ok', rc=0, errno=None)
    for record in r['validator_subprocess']['records']:
        if record['step_id'] == step['step_id']:
            record['operation'] = 'file-write-unlink'
    assert not validate(base), validate(base)
    chosen = select(steps(base), step_id=step['step_id'], order='query_first', observation='succeeded', operation_relation='matched')
    assert len(chosen) == 1 and chosen[0]['attempt']['requested_action'] == 'unlink', chosen
    records.append({'control': 'ordered_unlink', 'rejected': False})
    # No validator ran (its spawn failed): collection closed with nothing to
    # collect, the worker was released, and no row can claim an order.
    unordered = copy.deepcopy(base)
    unordered['data']['runner_result']['runner_subprocess']['ordering'].update(validator_disposition='not_spawned')
    unordered['data']['runner_result'].pop('validator_subprocess')
    for s in unordered['data']['runner_result']['steps']:
        s['sandbox_check'].update(result_source='synthetic', native_rc=None, errno=None, outcome='error', missing_reason='validator_not_invoked')
        s['comparison']['order'] = 'unestablished'
    assert not validate(unordered), validate(unordered)
    chosen = select(steps(unordered), step_id=step['step_id'], order='unestablished', observation='succeeded')
    assert len(chosen) == 1, chosen
    records.append({'control': 'unordered_unlink', 'rejected': False})
    claimed = copy.deepcopy(unordered)
    claimed['data']['runner_result']['steps'][0]['comparison']['order'] = 'query_first'
    errors = validate(claimed)
    assert any('lacks eligible record' in e for e in errors), errors
    records.append({'control': 'unordered_unlink_claims_order', 'rejected': True, 'errors': errors})
    (artifacts / 'mutation-order-controls.json').write_text(json.dumps(records, indent=2) + '\n')
    print(f'{target}: ordered and unordered unlink rows keep their records', flush=True)


def main():
    artifacts = Path(sys.argv[1])
    artifacts.mkdir(parents=True, exist_ok=True)
    check_cases(json.loads((ROOT / 'tests/fixtures/contract/path_diagnostics.json').read_text()))
    baseline = json.loads((FIXTURES / "checker/valid_run.json").read_text())
    prediction_error = "fs_write_allowed: expected sandbox_check allow"
    later_attempt_error = "mach_lookup_denied: expected attempt_ok=False"
    failures = []

    def check(name, envelope, diagnostics=(), case="BBX-001"):
        run_path = artifacts / f"{name}.json"
        run_path.write_text(json.dumps(envelope, indent=2) + "\n")
        result = subprocess.run(
            [sys.executable, str(CHECKER), str(run_path),
             str(FIXTURES / case / "expected.json")],
            capture_output=True, text=True, timeout=5,
        )
        output = result.stdout + result.stderr
        (artifacts / f"{name}.log").write_text(f"rc={result.returncode}\n{output}")
        expected_rc = 1 if diagnostics else 0
        if result.returncode != expected_rc or any(note not in output for note in diagnostics):
            failures.append(f"{name}: expected rc={expected_rc}, diagnostics={diagnostics!r}; "
                            f"got rc={result.returncode}, output={output!r}")
        else:
            print(f"{name}: ok", flush=True)

    check("valid", baseline)
    consumer_controls(artifacts, baseline)
    mutation_order_controls(artifacts, baseline)
    client_output_control(artifacts)
    cleanup_witness_controls(artifacts)
    from disposition_controls import run_controls
    run_controls(artifacts)
    for label, change, diagnostic in [
        ('missing_intent', lambda s: s['attempt'].pop('requested_action'), 'missing attempt.requested_action'),
        ('host_as_validator', lambda s: s['sandbox_check'].update(path_diagnostics={'input': s['sandbox_check']['filter_value'], 'observer': 'validator', 'phase': 'after_orchestration'}), 'path diagnostics lack host/phase provenance'),
    ]:
        lost = copy.deepcopy(baseline)
        change(lost['data']['runner_result']['steps'][0])
        check('current_' + label, lost, (diagnostic,))
    missing = copy.deepcopy(baseline)
    del missing["data"]["runner_result"]["steps"][0]["comparison"]
    check("current_missing_comparison", missing, ("fs_write_allowed: missing comparison",))

    broken = copy.deepcopy(baseline)
    attempt = broken["data"]["runner_result"]["steps"][2]["attempt"]
    attempt.update(outcome="ok", rc=0)
    check("wrong_later_attempt", broken, (later_attempt_error,))

    broken["data"]["runner_result"]["steps"][0]["sandbox_check"]["outcome"] = "deny"
    check("prediction_and_later_attempt", broken, (prediction_error, later_attempt_error))

    mismatch = copy.deepcopy(baseline)
    mismatch["data"]["runner_result"]["steps"][0]["sandbox_check"]["outcome"] = "deny"
    check("wrong_prediction", mismatch, (prediction_error,))

    broken = copy.deepcopy(mismatch)
    broken["data"]["runner_result"]["steps"][0]["attempt"].update(rc=-1)
    check("prediction_and_same_attempt", broken,
          (prediction_error, "fs_write_allowed: expected attempt_ok=True"))

    # Neither a malformed prediction object nor a missing attempt may prevent
    # the other channel or a sibling step from being checked.
    broken = copy.deepcopy(baseline)
    first, _, last = broken["data"]["runner_result"]["steps"]
    first["sandbox_check"] = None
    first["attempt"].update(rc=-1)
    del last["attempt"]
    check("malformed_channels", broken,
          ("missing sandbox_check for fs_write_allowed",
           "fs_write_allowed: expected attempt_ok=True", "missing attempt for mach_lookup_denied"))

    broken = copy.deepcopy(mismatch)
    broken["data"]["runner_result"]["steps"][2]["step_id"] = "fs_write_denied"
    check("prediction_and_duplicate_id", broken, (prediction_error, "expected step IDs in order"))

    broken = copy.deepcopy(baseline)
    broken["data"]["runner_result"]["steps"].reverse()
    check("reordered_steps", broken, ("expected step IDs in order",))

    missing = json.loads((FIXTURES / "checker/missing_path_run.json").read_text())
    check("expected_unavailable", missing, case="BBX-002")

    broken = copy.deepcopy(missing)
    broken["data"]["runner_result"]["steps"][2]["attempt"].update(rc=1)
    check("unavailable_and_later_attempt", broken,
          ("fs_read_allowed: expected attempt_ok=True",), case="BBX-002")

    broken = copy.deepcopy(missing)
    broken["data"]["runner_result"]["steps"][0]["sandbox_check"]["rc"] = 0
    check("unavailable_wrong_sentinel", broken,
          ("fs_read_missing: expected unavailable sandbox_check.rc=-1",), case="BBX-002")

    broken = copy.deepcopy(missing)
    broken["data"]["runner_result"]["steps"][0]["sandbox_check"].update(outcome="allow", rc=0, filter_type_id=1)
    check("invented_missing_path_prediction", broken,
          ("fs_read_missing: expected sandbox_check prediction_unavailable",), case="BBX-002")

    broken = copy.deepcopy(baseline)
    broken["data"]["runner_result"]["steps"][0]["sandbox_check"]["filter_type_id"] = None
    check("real_verdict_missing_filter_type", broken,
          ("fs_write_allowed: invalid sandbox_check.filter_type_id=None",))

    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()

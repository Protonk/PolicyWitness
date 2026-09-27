#!/usr/bin/env python3
"""Exercise the checker CLI with independently specified evidence and faults."""
import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests/fixtures/blackbox_e2e"
CHECKER = Path(__file__).with_name("validate_run.py")
sys.path.insert(0, str(ROOT / 'tests/lib'))
from consumer import recover_evidence, validate_evidence_shape, validate_current_build_evidence
from path_diagnostics_contract import check_cases
from worker_exit_witness import worker_exit_witness


def consumer_controls(artifacts, baseline, current):
    """Constructed JSON interpretation and bounded loss controls, not native proof."""
    records = []

    def run(name, envelope, expected, reject=False):
        path = artifacts / ('consumer_' + name + '.json')
        path.write_text(json.dumps(envelope, indent=2) + '\n')
        answers = recover_evidence(envelope)
        (artifacts / ('consumer_' + name + '.answers.json')).write_text(json.dumps(answers, indent=2) + '\n')
        try:
            expected(answers)
        except AssertionError as exc:
            assert reject, (name, str(exc))
            records.append({'control': name, 'rejected': True, 'reason': str(exc)})
        else:
            assert not reject, name + ': loss escaped its consumer expectation'
            records.append({'control': name, 'rejected': False})

    def require(condition, reason):
        assert condition, reason

    def agreement(a):
        require(a['comparison_groups']['agreement'] == ['fs_write_allowed'], 'supported agreement must remain recoverable')

    run('supported_agreement', current, agreement)
    unknown = copy.deepcopy(current)
    unknown['data']['runner_result']['steps'][0]['comparison']['conclusion'] = 'unavailable'
    unknown['data']['runner_result']['steps'][0]['drift'] = None
    # Even a shape-valid null projection must not erase independently expected agreement.
    assert not validate_evidence_shape(unknown)
    run('blanket_unknown', unknown, agreement, reject=True)

    # Conformance is explicitly requested for current builds. A stored schema-7
    # reply has the same wire version and must retain its historical meaning.
    legacy_difference = copy.deepcopy(current)
    s = legacy_difference['data']['runner_result']['steps'][0]
    s['sandbox_check'].update(outcome='deny', rc=1, native_rc=1, result_source='validator')
    s['attempt'].update(result_source='worker')
    s['comparison'].update(prediction='deny', conclusion='disagreement')
    s['drift'] = True
    assert not validate_evidence_shape(legacy_difference)
    run('legacy7_difference', legacy_difference,
        lambda a: require(a['steps'][0]['drift'] is True and
                          a['comparison_groups']['disagreement'] == ['fs_write_allowed'],
                          'historical schema-7 disagreement was reclassified'))

    def conformance(name, envelope, diagnostic=None):
        errors = validate_current_build_evidence(envelope)
        (artifacts / ('conformance_' + name + '.json')).write_text(json.dumps({
            'envelope': envelope, 'errors': errors}, indent=2) + '\n')
        assert (not errors if diagnostic is None else any(diagnostic in e for e in errors)), (name, errors)
        records.append({'control': name, 'rejected': bool(errors), 'errors': errors})

    conformance('unordered_difference', legacy_difference, 'current build cannot establish disagreement')
    limited = copy.deepcopy(legacy_difference)
    limited['data']['runner_result']['steps'][0]['comparison']['conclusion'] = 'unavailable'
    limited['data']['runner_result']['steps'][0]['drift'] = None
    conformance('unordered_difference_unavailable', limited)

    for prediction in ('allow', 'deny'):
        removed = copy.deepcopy(limited)
        s = removed['data']['runner_result']['steps'][0]
        s['sandbox_check'].update(operation='file-write-unlink', filter_kind='path', filter_value='/owned/A',
            outcome=prediction, rc=0 if prediction == 'allow' else 1, native_rc=0 if prediction == 'allow' else 1,
            path_diagnostics={'input':'/owned/A', 'same_as_input':[], 'realpath_resolved':None, 'firmlink_resolved':None, 'observer':'runner_host', 'phase':'after_orchestration'})
        s['attempt'].update(requested_action='unlink', requested_path='/owned/A', outcome='ok', rc=0)
        s['comparison'].update(prediction=prediction)
        s['comparison']['limitations'] += ['attempt_mutation_order_unestablished', 'host_path_resolution_changed']
        conformance('removed_' + prediction, removed)
        bad = copy.deepcopy(removed)
        b = bad['data']['runner_result']['steps'][0]
        b['comparison']['conclusion'] = 'agreement' if prediction == 'allow' else 'disagreement'
        b['drift'] = prediction == 'deny'
        conformance('removed_' + prediction + '_false_claim', bad, 'mutation uncertainty requires unavailable')
        for name, change, diagnostic in [
            ('different_target', lambda s: s['attempt'].update(requested_path='/owned/B'), 'unsupported attempt_mutation_order_unestablished'),
            ('failed_unlink', lambda s: s['attempt'].update(outcome='unlink_failed', rc=1), 'unsupported attempt_mutation_order_unestablished'),
            ('synthetic_attempt', lambda s: s['attempt'].update(result_source='synthetic'), 'unsupported attempt_mutation_order_unestablished'),
            ('later_resolves', lambda s: (s['sandbox_check']['path_diagnostics'].update(same_as_input=['realpath_resolved']), s['sandbox_check']['path_diagnostics'].pop('realpath_resolved')), 'unsupported host_path_resolution_changed'),
            ('later_resolves_elsewhere', lambda s: s['sandbox_check']['path_diagnostics'].update(realpath_resolved='/private/owned/A'), 'unsupported host_path_resolution_changed'),
            ('excluded', lambda s: s['sandbox_check'].update(outcome='prediction_unavailable'), 'unsupported host_path_resolution_changed'),
            ('dropped_resolution_change', lambda s: s['comparison']['limitations'].remove('host_path_resolution_changed'), 'missing host_path_resolution_changed'),
        ]:
            bad = copy.deepcopy(removed)
            change(bad['data']['runner_result']['steps'][0])
            conformance('removed_' + prediction + '_' + name, bad, diagnostic)
        # Recreation changes only the later-resolution observation; it cannot
        # erase the worker's mutation or certify runtime target identity.
        s['sandbox_check']['path_diagnostics']['same_as_input'] = ['realpath_resolved']
        del s['sandbox_check']['path_diagnostics']['realpath_resolved']
        s['comparison']['limitations'].remove('host_path_resolution_changed')
        conformance('recreated_' + prediction, removed)

    # Step position does not bound the confound while order is unestablished:
    # the worker can finish every attempt before the validator's first query,
    # so a later step's unlink confounds an earlier row naming the same target.
    def path_step(step_id, action, operation, prediction, conclusion, drift, limits):
        s = copy.deepcopy(limited['data']['runner_result']['steps'][0])
        s.update(step_id=step_id, drift=drift)
        s['sandbox_check'].update(operation=operation, filter_kind='path', filter_value='/owned/A',
            outcome=prediction, rc=0 if prediction == 'allow' else 1, native_rc=0 if prediction == 'allow' else 1,
            path_diagnostics={'input':'/owned/A', 'same_as_input':[], 'realpath_resolved':None, 'firmlink_resolved':None, 'observer':'runner_host', 'phase':'after_orchestration'})
        s['attempt'].update(requested_kind='file', requested_action=action, requested_path='/owned/A', outcome='ok', rc=0)
        s['comparison'].update(prediction=prediction, observation='succeeded', conclusion=conclusion,
            limitations=['query_attempt_order_unestablished', 'state_stability_unestablished',
                         'runtime_target_identity_unestablished'] + limits)
        return s

    uncertain = ['attempt_mutation_order_unestablished', 'host_path_resolution_changed']
    later = copy.deepcopy(limited)
    later['data']['runner_result']['steps'] = [
        path_step('read', 'open_read', 'file-read-data', 'allow', 'unavailable', None, uncertain),
        path_step('unlink', 'unlink', 'file-write-unlink', 'deny', 'unavailable', None, uncertain),
    ]
    conformance('later_unlink_confounds_earlier_row', later)
    claimed = copy.deepcopy(later)
    claimed['data']['runner_result']['steps'][0] = path_step(
        'read', 'open_read', 'file-read-data', 'allow', 'agreement', False, ['host_path_resolution_changed'])
    conformance('later_unlink_earlier_row_claims_agreement', claimed, 'missing attempt_mutation_order_unestablished')
    conformance('later_unlink_earlier_row_claims_agreement', claimed, 'mutation uncertainty requires unavailable')
    unrelated = copy.deepcopy(later)
    unrelated['data']['runner_result']['steps'][1]['attempt']['requested_path'] = '/owned/B'
    unrelated['data']['runner_result']['steps'][1]['sandbox_check'].update(filter_value='/owned/B')
    unrelated['data']['runner_result']['steps'][1]['sandbox_check']['path_diagnostics']['input'] = '/owned/B'
    conformance('later_unlink_of_other_target', unrelated, 'unsupported attempt_mutation_order_unestablished')


    missing = copy.deepcopy(current)
    step = missing['data']['runner_result']['steps'][0]
    step['drift'] = None
    step['comparison'].update(prediction='unavailable', observation='unavailable',
        observation_basis='no_completed_worker_result', conclusion='unavailable',
        target_relation='different_submitted', limitations=[
            'query_attempt_order_unestablished', 'state_stability_unestablished',
            'prediction:validator_no_verdict', 'attempt:slot_incomplete', 'target:different_submitted'])
    step['sandbox_check'].update(outcome='error', result_source='synthetic', native_rc=None, missing_reason='validator_no_verdict')
    step['attempt'].update(outcome='not_run_worker_died', result_source='synthetic', native_rc=None, missing_reason='slot_incomplete')

    def simultaneous(a):
        s = a['steps'][0]
        require({'prediction:validator_no_verdict', 'attempt:slot_incomplete', 'target:different_submitted'} <= set(s['comparison']['limitations']), 'all simultaneous limits are required')
        require(s['prediction_missing_reason'] == 'validator_no_verdict' and s['attempt_missing_reason'] == 'slot_incomplete', 'distinct missing reasons must survive')
        require(a['failure_groups']['missing_result'] == ['fs_write_allowed'], 'missing result is not an observed failure')

    run('simultaneous_limits', missing, simultaneous)
    lost = copy.deepcopy(missing)
    lost['data']['runner_result']['steps'][0]['comparison']['limitations'].remove('target:different_submitted')
    assert not validate_evidence_shape(lost)
    run('lost_one_limit', lost, simultaneous, reject=True)

    spawned = copy.deepcopy(current)
    s = spawned['data']['runner_result']['steps'][0]
    s['comparison'].update(observation_basis='spawned_child', limitations=[
        'query_attempt_order_unestablished', 'state_stability_unestablished',
        'exec_query_not_full_spawn_prediction', 'exec_result_failed_after_spawn', 'sandbox_attribution_unestablished'])
    s['attempt'].update(requested_kind='exec', requested_action='spawn', outcome='exec_failed',
        rc=37, child_pid=123, child_exit_code=37, stdout='controlled child marker')

    def child_failure(a):
        s = a['steps'][0]
        require(s['failed_after_spawn'] and s['failure'] == 'unattributed_failure', 'failed exec result must survive successful spawn')
        require(s['comparison']['conclusion'] == 'agreement' and s['attempt']['child_exit_code'] == 37, 'spawn comparison and child result are independent')

    run('failed_after_spawn', spawned, child_failure)
    lost = copy.deepcopy(spawned)
    lost['data']['runner_result']['steps'][0]['comparison']['limitations'].remove('exec_result_failed_after_spawn')
    run('lost_failed_exec', lost, child_failure, reject=True)

    for version in (4, 5, 6):
        old = copy.deepcopy(baseline)
        old['data']['runner_result']['schema_version'] = version
        # Deliberately populate the old boolean to test absence of a new meaning.
        old['data']['runner_result']['steps'][0]['drift'] = False
        old['data']['runner_result']['steps'][0]['sandbox_check']['path_diagnostics'] = {'input':'/old','realpath_resolved':'/old'}
        def legacy(a):
            require(a['comparison_groups']['agreement'] == [], 'old false does not imply response-7 agreement')
            require(len(a['failure_groups']['not_reported']) == 3, 'legacy derivation must stay unreported')
            require(a['steps'][0]['drift'] is False and a['steps'][0]['path_reporting'] == 'provenance_not_reported', 'legacy value/provenance changed')
        run('legacy_' + str(version), old, legacy)

    # New controller evidence can accompany an old runner reply.
    logged = copy.deepcopy(old)
    event = {'pid':42, 'operation':'file-write-data', 'path':'/attempt', 'raw_line':'controlled denial'}
    match = {'step_id':'fs_write_allowed', 'operation':'file-write-data', 'operation_source':'submitted_attempt',
             'requested_kind':'file', 'requested_action':'open_write', 'path':'/attempt', 'path_sources':['submitted_attempt.target']}
    window = {'kind':'runner_client_span', 'started_at_unix_ms':1000, 'ended_at_unix_ms':2500,
              'start':'1970-01-01 00:00:01+0000', 'end':'1970-01-01 00:00:03+0000',
              'event_timestamps_available':False, 'exact_run_membership':False, 'step_ordering':False, 'pid_reuse_protection':False}
    logged['data']['sandbox_log_capture'] = {'capture_status':'captured', 'window':window,
        'deny_events':[event, dict(event, pid=99)], 'step_denies':[{'event_index':0,
        'candidate_step_ids':['fs_write_allowed'], 'association':'candidate', 'matching_evidence':[match]}]}
    logged['data']['runner_sandbox_diagnostics'] = {'capture_status':'captured', 'correlation_status':'pid_match', 'termination_cause':'unknown'}

    def candidate(a, expected_window=window):
        d = a['denials']; c = d['candidates'][0]
        require(d['events'] == [event, dict(event,pid=99)], 'unmatched raw events must survive')
        require(c['event_index'] == 0 and c['event'] == event and c['association'] == 'candidate', 'candidate reference is not unique occurrence')
        require(c['matching_evidence'] == [match], 'matching provenance must survive')
        require(d['window'] == expected_window and d['diagnostics']['termination_cause'] == 'unknown', 'capture limits and unknown cause must survive')

    # Retain historical controller windows as well as old runner replies inside
    # current envelopes. Decoding must not reinterpret a stored trailing scan.
    old_window = dict(kind='trailing', last='10s', event_timestamps_available=False,
                      exact_run_membership=False, step_ordering=False, pid_reuse_protection=False)
    for envelope_version, recorded_window in [(1, old_window), (2, window)]:
        historical = copy.deepcopy(logged)
        historical['schema_version'] = envelope_version
        historical['data']['sandbox_log_capture']['window'] = recorded_window
        if envelope_version == 1:
            historical['data']['log_last'] = '10s'
        else:
            historical['data'].pop('log_last', None)
        run('envelope_%d_with_legacy_runner_candidates' % envelope_version, historical,
            lambda a: candidate(a, recorded_window))
    logged['schema_version'] = 2
    logged['data'].pop('log_last', None)
    lost = copy.deepcopy(logged)
    del lost['data']['sandbox_log_capture']['step_denies'][0]['matching_evidence'][0]['operation_source']
    run('lost_matching_owner', lost, candidate, reject=True)
    lost = copy.deepcopy(logged)
    lost['data']['sandbox_log_capture']['window']['exact_run_membership'] = True
    run('invented_exact_run', lost, candidate, reject=True)
    for status, correlation in [('captured','no_match'), ('blocked','unavailable'),
                                ('requested_unavailable','unavailable'), ('disabled','not_attempted'), ('no_worker','not_attempted')]:
        absent = copy.deepcopy(logged)
        absent['data']['runner_sandbox_diagnostics'].update(capture_status=status, correlation_status=correlation)
        absent['data']['sandbox_log_capture'] = (dict(capture_status=status, window=window,
            deny_events=[dict(event,pid=99)] if status=='captured' else None,
            step_denies=[] if status=='captured' else None, blocked_reason='controlled blockage' if status=='blocked' else None)
            if status not in ('disabled','no_worker') else None)
        def availability(a):
            d=a['denials']
            require((d['capture_status'],d['correlation_status']) == (status,correlation), 'capture states must remain distinct')
            require(d['candidates'] == ([] if status=='captured' else None), 'no match and no report differ')
            if status=='blocked': require(d['capture']['blocked_reason']=='controlled blockage', 'capture detail lost')
        run('capture_'+status, absent, availability)
    for name, runner, state in [('no_reply',None,'no_runner_reply'), ('no_steps',{'schema_version':7,'steps':[]},'no_admitted_steps')]:
        run(name, {'data':{'runner_result':runner}}, lambda a: require(a['step_reporting']==state and a['steps']==[], 'run absence must not invent step comparisons'))
    (artifacts / 'consumer-controls.json').write_text(json.dumps(records, indent=2) + '\n')


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


def ordering_controls(artifacts):
    """Handwritten response-8 chain with one independently specified native record."""
    query = dict(operation='file-read-data', filter_kind='path', filter_value='/owned',
                 outcome='allow', result_source='validator', native_rc=0, rc=0, errno=0, pid=42)
    record = dict(step_id='s', operation='file-read-data', filter_type='PATH', filter_value='/owned',
                  outcome='allow', rc=0, errno=0)
    ordering = dict(collection_closed_before_proceed=True, proceed_set=True, proceed_observed=True,
                    validator_disposition='reaped', worker_lifetime_established=True, protocol_violations=[])
    step = dict(step_id='s', sandbox_check=query, attempt=dict(requested_kind='file', requested_action='open_read'),
        drift=False, comparison=dict(scope='submitted_operation_and_target', prediction='allow', observation='succeeded',
        observation_basis='completed_worker_status', operation_relation='matched', target_relation='same_submitted',
        conclusion='agreement', order='query_first', limitations=['state_stability_unestablished', 'runtime_target_identity_unestablished']))
    base = dict(schema_version=8, sandboxed_after_apply=True, steps=[step], runner_subprocess=dict(pid=42, ordering=ordering),
                validator_subprocess=dict(reaped=True, records=[record]))
    def check(name, change=lambda r: None, reject=False):
        runner = copy.deepcopy(base); change(runner)
        envelope = dict(data=dict(runner_result=runner))
        errors = validate_evidence_shape(envelope)
        (artifacts / ('order8_' + name + '.json')).write_text(json.dumps(dict(envelope=envelope, errors=errors), indent=2) + '\n')
        assert bool(errors) == reject, (name, errors)
    check('eligible')
    for field in ['collection_closed_before_proceed', 'proceed_set', 'proceed_observed', 'worker_lifetime_established']:
        check('missing_' + field, lambda r, f=field: r['runner_subprocess']['ordering'].update({f:False}), True)
    check('failed_apply', lambda r: r.update(sandboxed_after_apply=False), True)
    check('missing_ordering', lambda r: r['runner_subprocess'].pop('ordering'), True)
    check('missing_order', lambda r: r['steps'][0]['comparison'].pop('order'), True)
    check('synthetic', lambda r: r['steps'][0]['sandbox_check'].update(result_source='synthetic'), True)
    check('native_error', lambda r: r['steps'][0]['sandbox_check'].update(outcome='error', native_rc=-1, rc=-1), True)
    check('unknown_outcome', lambda r: r['steps'][0]['sandbox_check'].update(outcome='future'), True)
    check('incoherent_native', lambda r: r['steps'][0]['sandbox_check'].update(native_rc=1), True)
    check('missing_native_errno', lambda r: r['steps'][0]['sandbox_check'].pop('errno'), True)
    check('duplicate', lambda r: r['validator_subprocess']['records'].append(copy.deepcopy(record)), True)
    check('wrong_tuple', lambda r: r['validator_subprocess']['records'][0].update(filter_value='/other'), True)
    check('wrong_pid', lambda r: r['steps'][0]['sandbox_check'].update(pid=43), True)
    check('order_limit', lambda r: r['steps'][0]['comparison']['limitations'].append('query_attempt_order_unestablished'), True)
    def unordered(r):
        r['steps'][0]['comparison'].update(order='unestablished')
        r['steps'][0]['comparison']['limitations'].append('query_attempt_order_unestablished')
    check('unsupported_unestablished', unordered, True)
    def no_worker(r):
        unordered(r); r.pop('runner_subprocess'); r.pop('validator_subprocess')
        r['steps'][0]['sandbox_check'].update(result_source='synthetic', native_rc=None, pid=None)
    check('no_worker', no_worker)
    def fault(r):
        unordered(r)
        r['runner_subprocess']['ordering'].update(proceed_set=False, protocol_violations=['acknowledgement_without_release'])
    check('raw_contradiction_retained', fault)
    def diagnostic(r):
        unordered(r); r['steps'][0]['sandbox_check'].update(outcome='error', native_rc=-1, rc=-1)
        r['validator_subprocess']['records'][0].update(outcome='error', rc=-1)
    check('diagnostic_unestablished', diagnostic)
    def difference(r):
        r['steps'][0]['comparison'].update(conclusion='disagreement', limitations=[])
        r['steps'][0]['drift'] = True
    check('disagreement_without_labels', difference, True)
    def uncertain_cleanup(r):
        r['runner_subprocess']['ordering'].update(validator_disposition='unconfirmed')
        r['validator_subprocess'].update(reaped=False)
    check('unconfirmed_cleanup_still_ordered', uncertain_cleanup)

    # Reporting failures retain diagnostic observations but certify no comparisons.
    failed = copy.deepcopy(base)
    failed.update(rc=1, normalized_outcome='runner_reporting_failed', error='host invariant rejected',
        reporting_failure=dict(origin='runner_host', diagnostic='missing ordering', original_rc=0,
            original_normalized_outcome='ok', original_error=None, evidence_retained=True))
    failed['runner_subprocess'].pop('ordering')
    failed['steps'][0].pop('comparison'); failed['steps'][0]['drift'] = None
    def report_check(name, change=lambda r: None, reject=False):
        runner = copy.deepcopy(failed); change(runner)
        envelope = dict(data=dict(runner_result=runner))
        errors = validate_evidence_shape(envelope)
        (artifacts / ('reply_failure_' + name + '.json')).write_text(json.dumps(dict(envelope=envelope, errors=errors), indent=2) + '\n')
        assert bool(errors) == reject, (name, errors)
        return recover_evidence(envelope)
    recovered = report_check('preserved')
    assert recovered['step_reporting'] == 'reporting_failed'
    assert recovered['comparison_groups']['not_reported'] == ['s']
    assert recovered['steps'][0]['query'] == query
    assert recovered['steps'][0]['attempt'] == step['attempt']
    report_check('false_drift', lambda r: r['steps'][0].update(drift=False), True)
    report_check('true_drift', lambda r: r['steps'][0].update(drift=True), True)
    report_check('missing_drift', lambda r: r['steps'][0].pop('drift'), True)
    report_check('comparison', lambda r: r['steps'][0].update(comparison=copy.deepcopy(step['comparison'])), True)
    report_check('ok', lambda r: r.update(normalized_outcome='ok'), True)
    report_check('rc', lambda r: r.update(rc=0), True)
    report_check('missing_marker', lambda r: r.pop('reporting_failure'), True)
    report_check('bad_marker', lambda r: r.update(reporting_failure='invalid'), True)
    for key in ['origin', 'diagnostic', 'original_rc', 'original_normalized_outcome', 'evidence_retained']:
        report_check('missing_' + key, lambda r, k=key: r['reporting_failure'].pop(k), True)
    report_check('false_retention', lambda r: r['reporting_failure'].update(evidence_retained=False), True)
    def minimal(r):
        r['reporting_failure']['evidence_retained'] = False
        r['steps'] = []; r.pop('runner_subprocess'); r.pop('validator_subprocess')
    report_check('minimal', minimal)

    # Preserve the host's raw launch evidence without an errno-name allowlist or
    # interpreting its diagnostic. Older envelopes remain explicitly unreported.
    spawn = dict(origin='runner_host', operation='posix_spawn',
        executable_path='/unknown/validator-"é"', return_code=2147483647,
        diagnostic='unfamiliar native launch diagnostic')
    def spawn_failed(r):
        unordered(r)
        r.update(rc=1, normalized_outcome='validator_spawn_failed', error='native launch failure',
                 validator_spawn_failure=copy.deepcopy(spawn))
        r.pop('validator_subprocess')
        r['runner_subprocess']['ordering']['validator_disposition'] = 'not_spawned'
        r['steps'][0]['sandbox_check'].update(outcome='error', result_source='synthetic',
            native_rc=None, errno=None, missing_reason='validator_not_invoked')
        r['steps'][0]['comparison'].update(prediction='unavailable', conclusion='unavailable')
        r['steps'][0]['drift'] = None
    check('unfamiliar_spawn_failure', spawn_failed)
    runner = copy.deepcopy(base); spawn_failed(runner)
    envelope = dict(data=dict(runner_result=runner))
    recovered = recover_evidence(envelope)
    assert recovered['validator_spawn_failure'] == spawn
    runner['validator_spawn_failure']['return_code'] = 2
    assert recovered['validator_spawn_failure'] == spawn, 'recovery aliases its input'
    runner.pop('validator_spawn_failure')
    assert not validate_evidence_shape(envelope), 'older response-8 replies may omit spawn evidence'
    assert recover_evidence(envelope)['validator_spawn_failure'] is None
    def retained_spawn(r):
        r.pop('validator_subprocess')
        r['steps'][0]['sandbox_check'].update(outcome='error', result_source='synthetic', native_rc=None)
        r['reporting_failure'].update(original_rc=1, original_normalized_outcome='validator_spawn_failed',
                                     original_error='native launch failure')
        r['validator_spawn_failure'] = copy.deepcopy(spawn)
    assert report_check('retained_spawn', retained_spawn)['validator_spawn_failure'] == spawn
    def false_spawn_retention(r):
        minimal(r); r['validator_spawn_failure'] = copy.deepcopy(spawn)
    report_check('minimal_with_spawn_evidence', false_spawn_retention, True)
    # The record's shape is checked, not its meaning: any nonzero code is a failure.
    for name, change in [
        ('zero_code', lambda r: r['validator_spawn_failure'].update(return_code=0)),
        ('string_code', lambda r: r['validator_spawn_failure'].update(return_code='2')),
        ('missing_path', lambda r: r['validator_spawn_failure'].pop('executable_path')),
        ('foreign_origin', lambda r: r['validator_spawn_failure'].update(origin='validator')),
        ('with_subprocess', lambda r: r.update(validator_subprocess=dict(reaped=True, records=[]))),
    ]:
        def malformed(r, change=change):
            spawn_failed(r); change(r)
        check('malformed_spawn_' + name, malformed, True)

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

    current = copy.deepcopy(baseline)
    current["data"]["runner_result"]["schema_version"] = 7
    for i, step in enumerate(current["data"]["runner_result"]["steps"]):
        step["attempt"].update(requested_kind="mach_lookup" if i == 2 else "file",
                               requested_action="bootstrap_look_up" if i == 2 else "open_write")
        step["drift"] = False if i == 0 else None
        step["comparison"] = dict(scope="submitted_operation_and_target",
            prediction="allow" if i == 0 else "deny",
            observation="succeeded" if i == 0 else "permission_failure",
            observation_basis="completed_worker_status" if i == 0 else "permission_errno",
            operation_relation="matched", target_relation="same_submitted",
            conclusion="agreement" if i == 0 else "directional_consistency",
            limitations=["query_attempt_order_unestablished", "state_stability_unestablished"])
        if i != 0:
            step['comparison']['limitations'].append('sandbox_attribution_unestablished')
        paths = step["sandbox_check"].get("path_diagnostics")
        if paths is not None:
            paths.update(observer="runner_host", phase="after_orchestration")
    check("response7", current)
    consumer_controls(artifacts, baseline, current)
    ordering_controls(artifacts)
    cleanup_witness_controls(artifacts)
    from disposition_controls import run_controls
    run_controls(artifacts)
    for label, change, diagnostic in [
        ('missing_intent', lambda s: s['attempt'].pop('requested_action'), 'missing attempt.requested_action'),
        ('missing_temporal_limit', lambda s: s['comparison']['limitations'].remove('state_stability_unestablished'), 'missing comparison limitation state_stability_unestablished'),
        ('host_as_validator', lambda s: s['sandbox_check'].update(path_diagnostics={'input':'/owned','observer':'validator','phase':'after_orchestration'}), 'path diagnostics lack host/phase provenance'),
    ]:
        lost = copy.deepcopy(current)
        change(lost['data']['runner_result']['steps'][0])
        check('response7_' + label, lost, (diagnostic,))
    lost = copy.deepcopy(current)
    lost['data']['runner_result']['steps'][1]['comparison']['limitations'].remove('sandbox_attribution_unestablished')
    check('response7_missing_attribution_limit', lost,
          ('missing comparison limitation sandbox_attribution_unestablished',))
    missing = copy.deepcopy(current)
    del missing["data"]["runner_result"]["steps"][0]["comparison"]
    check("response7_missing_comparison", missing, ("fs_write_allowed: missing comparison",))
    broken_current = copy.deepcopy(current)
    first, _, last = broken_current["data"]["runner_result"]["steps"]
    first["sandbox_check"] = None
    last["attempt"] = None
    check("response7_malformed_independent_channels", broken_current,
          ("missing sandbox_check for fs_write_allowed", "missing attempt for mach_lookup_denied"))

    broken = copy.deepcopy(baseline)
    attempt = broken["data"]["runner_result"]["steps"][2]["attempt"]
    attempt.update(outcome="ok", rc=0, exit_code=0)
    check("wrong_later_attempt", broken, (later_attempt_error,))

    broken["data"]["runner_result"]["steps"][0]["sandbox_check"]["outcome"] = "deny"
    check("prediction_and_later_attempt", broken, (prediction_error, later_attempt_error))

    mismatch = copy.deepcopy(baseline)
    mismatch["data"]["runner_result"]["steps"][0]["sandbox_check"]["outcome"] = "deny"
    check("wrong_prediction", mismatch, (prediction_error,))

    broken = copy.deepcopy(mismatch)
    broken["data"]["runner_result"]["steps"][0]["attempt"].update(rc=-1, exit_code=-1)
    check("prediction_and_same_attempt", broken,
          (prediction_error, "fs_write_allowed: expected attempt_ok=True"))

    # Neither a malformed prediction object nor a missing attempt may prevent
    # the other channel or a sibling step from being checked.
    broken = copy.deepcopy(baseline)
    first, _, last = broken["data"]["runner_result"]["steps"]
    first["sandbox_check"] = None
    first["attempt"].update(rc=-1, exit_code=-1)
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
    broken["data"]["runner_result"]["steps"][2]["attempt"].update(rc=1, exit_code=1)
    check("unavailable_and_later_attempt", broken,
          ("fs_read_allowed: expected attempt_ok=True",), case="BBX-002")

    broken = copy.deepcopy(missing)
    del broken["data"]["runner_result"]["steps"][0]["drift"]
    check("unavailable_missing_drift", broken,
          ("fs_read_missing: expected unavailable prediction to have explicit drift=null",), case="BBX-002")

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

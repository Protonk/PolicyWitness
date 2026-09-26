"""Recover documented evidence from one JSON envelope, without native classifiers.

No policy, specimen, errno rules, files or production implementation are inputs.
Scenario expectations belong to callers. Legacy absences remain unreported.
"""
from copy import deepcopy


def recover_evidence(envelope):
    data = envelope.get('data') or {}
    runner = data.get('runner_result')
    steps = (runner or {}).get('steps')
    answer = {
        'schema_version': (runner or {}).get('schema_version'),
        'reporting_failure': (runner or {}).get('reporting_failure'),
        'validator_spawn_failure': (runner or {}).get('validator_spawn_failure'),
        'step_reporting': ('reporting_failed' if (runner or {}).get('reporting_failure') is not None else
                           'no_runner_reply' if runner is None else
                           'not_reported' if steps is None else
                           'reported' if steps else 'no_admitted_steps'),
        'comparison_groups': {key: [] for key in
            ('agreement', 'disagreement', 'directional_consistency', 'unavailable', 'not_reported')},
        'failure_groups': {key: [] for key in ('unattributed_failure', 'missing_result', 'not_reported')},
        'steps': [],
    }
    for step in steps or []:
        comparison = step.get('comparison')
        attempt = step.get('attempt') or {}
        query = step.get('sandbox_check') or {}
        conclusion = (comparison or {}).get('conclusion', 'not_reported')
        answer['comparison_groups'].setdefault(conclusion, []).append(step['step_id'])
        limits = (comparison or {}).get('limitations') or []
        observation = (comparison or {}).get('observation')
        failed_after_spawn = 'exec_result_failed_after_spawn' in limits
        failure = None
        if comparison is None:
            failure = 'not_reported'
        elif observation == 'unavailable':
            failure = 'missing_result'
        elif (observation in ('permission_failure', 'other_failure') or failed_after_spawn) and \
                'sandbox_attribution_unestablished' in limits:
            failure = 'unattributed_failure'
        if failure is not None:
            answer['failure_groups'][failure].append(step['step_id'])
        path = query.get('path_diagnostics')
        answer['steps'].append({
            'step_id': step['step_id'], 'comparison': comparison,
            'drift_present': 'drift' in step, 'drift': step.get('drift'),
            'query': query, 'attempt': attempt,
            'failure': failure, 'failed_after_spawn': failed_after_spawn,
            'prediction_missing_reason': query.get('missing_reason'),
            'attempt_missing_reason': attempt.get('missing_reason'),
            'path_reporting': ('not_reported' if path is None else
                               'provenance_not_reported' if path.get('observer') is None or path.get('phase') is None
                               else 'reported'),
            'path_diagnostics': path,
        })
    capture = data.get('sandbox_log_capture') or {}
    diagnostics = data.get('runner_sandbox_diagnostics') or {}
    events = capture.get('deny_events')
    associations = capture.get('step_denies')
    candidates = None
    if associations is not None:
        candidates = []
        for association in associations:
            index = association.get('event_index')
            event = events[index] if isinstance(events, list) and type(index) is int and 0 <= index < len(events) else None
            candidates.append(dict(association, event=event))
    answer['denials'] = {
        'capture_status': diagnostics.get('capture_status', capture.get('capture_status', 'not_reported')),
        'correlation_status': diagnostics.get('correlation_status', 'not_reported'),
        'window': capture.get('window'), 'events': events, 'candidates': candidates,
        'event_reporting': 'reported' if events is not None else 'not_reported',
        'association_reporting': 'reported' if associations is not None else 'not_reported',
        'diagnostics': data.get('runner_sandbox_diagnostics'),
        # Preserve capture/observer errors as well as status and candidate summaries.
        'capture': data.get('sandbox_log_capture'),
    }
    return deepcopy(answer)


def validate_evidence_shape(envelope):
    """Universal response guarantees; no prediction/attempt classification."""
    runner = (envelope.get('data') or {}).get('runner_result') or {}
    if type(runner.get('schema_version')) is not int or runner['schema_version'] < 7:
        return []
    errors = []
    failure = runner.get('reporting_failure')
    failed_reporting = failure is not None
    if failed_reporting or runner.get('normalized_outcome') == 'runner_reporting_failed':
        if runner['schema_version'] != 8 or runner.get('normalized_outcome') != 'runner_reporting_failed' or \
                type(runner.get('rc')) is not int or runner['rc'] != 1 or \
                not isinstance(runner.get('error'), str) or not runner['error']:
            errors.append('reporting failure requires a failed summary and diagnostic')
        if not isinstance(failure, dict) or failure.get('origin') != 'runner_host' or \
                not isinstance(failure.get('diagnostic'), str) or not failure['diagnostic'] or \
                type(failure.get('original_rc')) is not int or \
                not isinstance(failure.get('original_normalized_outcome'), str) or not failure['original_normalized_outcome'] or \
                (failure.get('original_error') is not None and not isinstance(failure['original_error'], str)) or \
                type(failure.get('evidence_retained')) is not bool:
            errors.append('invalid reporting_failure diagnostics')
        elif not failure['evidence_retained'] and (runner.get('steps') != [] or
                runner.get('runner_subprocess') is not None or runner.get('validator_subprocess') is not None or
                runner.get('validator_spawn_failure') is not None):
            errors.append('reporting failure without evidence retention must omit steps, subprocesses and validator spawn evidence')
    spawn = runner.get('validator_spawn_failure')
    if spawn is not None:
        if not isinstance(spawn, dict) or spawn.get('origin') != 'runner_host' or \
                spawn.get('operation') != 'posix_spawn' or \
                not isinstance(spawn.get('executable_path'), str) or not spawn['executable_path'] or \
                type(spawn.get('return_code')) is not int or spawn['return_code'] == 0 or \
                not isinstance(spawn.get('diagnostic'), str):
            errors.append('invalid validator_spawn_failure record')
        elif runner.get('validator_subprocess') is not None:
            errors.append('validator_spawn_failure cannot coexist with a validator subprocess')
    values = {
        'scope': {'submitted_operation_and_target'},
        'prediction': {'allow', 'deny', 'unavailable'},
        'observation': {'succeeded', 'permission_failure', 'other_failure', 'unavailable'},
        'observation_basis': {'completed_worker_status', 'permission_errno', 'bootstrap_permission_result', 'spawned_child', 'no_completed_worker_result'},
        'operation_relation': {'matched', 'different', 'unresolved'},
        'target_relation': {'same_submitted', 'different_submitted', 'unresolved'},
        'conclusion': {'agreement', 'disagreement', 'directional_consistency', 'unavailable'},
    }
    for step in runner.get('steps') or []:
        if not isinstance(step, dict):
            errors.append('step is not an object')
            continue
        sid = step.get('step_id')
        comparison = step.get('comparison')
        if failed_reporting:
            if comparison is not None or 'drift' not in step or step['drift'] is not None:
                errors.append(f'{sid}: reporting failure must withhold every comparison and drift claim')
        elif not isinstance(comparison, dict):
            errors.append(f'{sid}: missing comparison')
        else:
            for key, allowed in values.items():
                if not isinstance(comparison.get(key), str) or comparison[key] not in allowed:
                    errors.append(f'{sid}: invalid comparison.{key}')
            limits = comparison.get('limitations')
            if not isinstance(limits, list) or any(not isinstance(x, str) for x in limits):
                errors.append(f'{sid}: invalid comparison.limitations')
            else:
                required = {'state_stability_unestablished'}
                if runner['schema_version'] < 8 or comparison.get('order') != 'query_first':
                    required.add('query_attempt_order_unestablished')
                if comparison.get('observation') in ('permission_failure', 'other_failure') or 'exec_result_failed_after_spawn' in limits:
                    required.add('sandbox_attribution_unestablished')
                for limit in sorted(required - set(limits)):
                    errors.append(f'{sid}: missing comparison limitation {limit}')
            projection = {'agreement': False, 'disagreement': True}.get(comparison.get('conclusion'))
            if 'drift' not in step or step['drift'] is not projection:
                errors.append(f'{sid}: drift does not project comparison.conclusion')
        attempt = step.get('attempt') or {}
        for key in ('requested_kind', 'requested_action'):
            if not isinstance(attempt, dict) or not isinstance(attempt.get(key), str):
                errors.append(f'{sid}: missing attempt.{key}')
        query = step.get('sandbox_check') or {}
        path = query.get('path_diagnostics') if isinstance(query, dict) else None
        if path is not None and (not isinstance(path, dict) or
                (path.get('observer'), path.get('phase')) != ('runner_host', 'after_orchestration')):
            errors.append(f'{sid}: path diagnostics lack host/phase provenance')
    if runner['schema_version'] >= 8 and not failed_reporting:
        errors.extend(validate_ordering(runner))
    return errors


def validate_current_build_evidence(envelope):
    """Explicit producer conformance, separate from historical response decoding.

    Current response-7 producers establish no query order. The unchanged wire
    version alone cannot distinguish them from stored replies that report the
    weaker historical disagreement. Call this only for a known current build.

    Removal evidence is gathered from every step before any step is judged:
    with order unestablished, an attempt in any step may precede any query, so
    a later step's unlink confounds an earlier row naming the same target.
    """
    errors = validate_evidence_shape(envelope)
    runner = (envelope.get('data') or {}).get('runner_result') or {}
    steps = [step for step in runner.get('steps') or [] if isinstance(step, dict)]
    removed_targets = set()
    for step in steps:
        attempt = step.get('attempt') or {}
        if isinstance(attempt, dict) and attempt.get('result_source') == 'worker' and \
                (attempt.get('requested_kind'), attempt.get('requested_action'), attempt.get('outcome')) == ('file', 'unlink', 'ok') and \
                type(attempt.get('rc')) is int and attempt['rc'] == 0 and \
                isinstance(attempt.get('requested_path'), str):
            removed_targets.add(attempt['requested_path'])
    for step in steps:
        comparison = step.get('comparison')
        query = step.get('sandbox_check')
        if not isinstance(comparison, dict) or not isinstance(query, dict):
            continue
        limits = comparison.get('limitations')
        if not isinstance(limits, list) or any(not isinstance(x, str) for x in limits):
            continue
        sid = step.get('step_id')
        if comparison.get('conclusion') == 'disagreement':
            errors.append(f'{sid}: current build cannot establish disagreement without state and identity evidence')
        planned_path = query.get('filter_kind') == 'path' and \
            isinstance(query.get('filter_value'), str) and bool(query['filter_value']) and \
            query.get('outcome') != 'prediction_unavailable'
        mutation = planned_path and query['filter_value'] in removed_targets and comparison.get('order') != 'query_first'
        if 'attempt_mutation_order_unestablished' in limits and not mutation:
            errors.append(f'{sid}: unsupported attempt_mutation_order_unestablished')
        if mutation and 'attempt_mutation_order_unestablished' not in limits:
            errors.append(f'{sid}: missing attempt_mutation_order_unestablished')
        if mutation and comparison.get('observation') == 'succeeded' and comparison.get('conclusion') != 'unavailable':
            errors.append(f'{sid}: mutation uncertainty requires unavailable comparison')
        path = query.get('path_diagnostics')
        host_nonresolution = planned_path and isinstance(path, dict) and \
            (path.get('observer'), path.get('phase')) == ('runner_host', 'after_orchestration') and \
            path.get('realpath_resolved') is None
        if 'host_path_resolution_changed' in limits and not host_nonresolution:
            errors.append(f'{sid}: unsupported host_path_resolution_changed')
        if host_nonresolution and 'host_path_resolution_changed' not in limits:
            errors.append(f'{sid}: missing host_path_resolution_changed')
    return errors


def validate_ordering(runner):
    """Response-8 chain and native-record eligibility; booleans describe observations."""
    errors = []
    worker = runner.get('runner_subprocess')
    validator = runner.get('validator_subprocess') or {}
    ordering = worker.get('ordering') if isinstance(worker, dict) else None
    chain = False
    if isinstance(worker, dict):
        if not isinstance(ordering, dict):
            errors.append('response 8 requires runner_subprocess.ordering')
        else:
            for key in ('collection_closed_before_proceed', 'proceed_set', 'proceed_observed', 'worker_lifetime_established'):
                if type(ordering.get(key)) is not bool:
                    errors.append('invalid ordering.' + key)
            disposition = ordering.get('validator_disposition')
            if disposition not in {'not_invoked', 'not_needed', 'not_spawned', 'reaped', 'unconfirmed'}:
                errors.append('invalid ordering.validator_disposition')
            faults = ordering.get('protocol_violations')
            if not isinstance(faults, list) or any(not isinstance(x, str) for x in faults):
                errors.append('invalid ordering.protocol_violations')
                faults = []
            c, s, o = (ordering.get(k) is True for k in ('collection_closed_before_proceed', 'proceed_set', 'proceed_observed'))
            contradictions = []
            if s and not c: contradictions.append('release_without_collection_closure')
            if o and not s: contradictions.append('acknowledgement_without_release')
            if (s or o) and runner.get('sandboxed_after_apply') is not True:
                contradictions.append('release_without_successful_application')
            failure = ((worker.get('worker_evidence') or {}).get('failure') or {})
            if failure.get('operation') == 11 and (o or any((x.get('attempt') or {}).get('result_source') == 'worker' for x in runner.get('steps', []))):
                contradictions.append('attempt_or_acknowledgement_after_proceed_failure')
            for fault in contradictions:
                if fault not in faults: errors.append('unmarked ordering protocol violation: ' + fault)
            if c != (disposition != 'not_invoked'):
                errors.append('ordering collection decision disagrees with validator disposition')
            if disposition == 'reaped' and validator.get('reaped') is not True:
                errors.append('ordering reaped disposition lacks validator reap evidence')
            if disposition == 'unconfirmed' and (not validator or validator.get('reaped') is not False):
                errors.append('ordering unconfirmed disposition lacks validator evidence')
            if disposition in {'not_needed', 'not_spawned', 'not_invoked'} and validator:
                errors.append('ordering terminal decision contradicts validator subprocess')
            chain = c and s and o and ordering.get('worker_lifetime_established') is True and not faults and not contradictions and runner.get('sandboxed_after_apply') is True
    records = validator.get('records') or []
    for step in runner.get('steps') or []:
        if not isinstance(step, dict): continue
        comparison, query = step.get('comparison') or {}, step.get('sandbox_check') or {}
        if not isinstance(comparison, dict) or not isinstance(query, dict): continue
        sid = step.get('step_id')
        order = comparison.get('order')
        limits = comparison.get('limitations') or []
        if not isinstance(order, str): errors.append(f'{sid}: missing comparison.order')
        if ('query_attempt_order_unestablished' in limits) != (order != 'query_first'):
            errors.append(f'{sid}: order limitation disagrees with comparison.order')
        if comparison.get('conclusion') == 'disagreement' or step.get('drift') is True:
            errors.append(f'{sid}: response 8 cannot establish disagreement')
        rc, err = query.get('native_rc'), query.get('errno')
        native = type(rc) is int and type(err) is int and query.get('rc') == rc and (
            (query.get('outcome') == 'allow' and rc == 0) or
            (query.get('outcome') == 'deny' and rc == 1 and err == 0))
        matches = [r for r in records if isinstance(r, dict) and r.get('step_id') == sid]
        associated = len(matches) == 1 and all(matches[0].get(k) == v for k, v in {
            'operation': query.get('operation'), 'filter_type': str(query.get('filter_kind')).upper(),
            'filter_value': None if query.get('filter_kind') == 'none' else query.get('filter_value'), 'outcome': query.get('outcome'),
            'rc': rc, 'errno': err}.items())
        eligible = chain and query.get('result_source') == 'validator' and native and associated and query.get('pid') == worker.get('pid')
        if order == 'query_first' and not eligible:
            errors.append(f'{sid}: query_first lacks eligible record or ordering chain')
        if order == 'unestablished' and eligible:
            errors.append(f'{sid}: eligible record with complete chain requires query_first')
    return errors

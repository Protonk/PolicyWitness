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
        'step_reporting': ('no_runner_reply' if runner is None else
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
        if not isinstance(comparison, dict):
            errors.append(f'{sid}: missing comparison')
        else:
            for key, allowed in values.items():
                if not isinstance(comparison.get(key), str) or comparison[key] not in allowed:
                    errors.append(f'{sid}: invalid comparison.{key}')
            limits = comparison.get('limitations')
            if not isinstance(limits, list) or any(not isinstance(x, str) for x in limits):
                errors.append(f'{sid}: invalid comparison.limitations')
            else:
                required = {'query_attempt_order_unestablished', 'state_stability_unestablished'}
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
    return errors

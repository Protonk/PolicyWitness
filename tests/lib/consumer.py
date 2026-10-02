"""Read one JSON document: a controller envelope or a bare runner reply.

The document's versions are checked before anything else is interpreted. A
supported document is validated against the current contract; evidence is then
selected by field. No policy, specimen, errno rule, file or production
implementation is an input, and nothing here asserts agreement or disagreement
between the prediction and the attempt. Scenario expectations belong to callers.

Public functions:

    validate(document)  -> [error, ...]   one version error, or the shape errors
    steps(document)     -> [step, ...]    the reply's steps after the version gate
    select(steps, ...)  -> [step, ...]    steps whose fields equal the given values
    lifecycle(document) -> view           the registered lifecycle account
    denials(document)   -> dict           the optional log channel, resolved in place
"""
from copy import deepcopy

import contract
import lifecycle_contract
from lifecycle_adapter import read_lifecycle, summaries


# The comparison record vocabulary (docs/PolicyWitness.md, "Reading a comparison record").
OBSERVATIONS = ('succeeded', 'permission_failure', 'other_failure', 'unavailable')
OBSERVATION_BASES = ('completed_worker_status', 'permission_errno', 'bootstrap_permission_result',
                     'spawned_child', 'no_completed_worker_result')
OPERATION_RELATIONS = ('matched', 'different', 'unresolved')
TARGET_RELATIONS = ('same_submitted', 'different_submitted', 'unresolved')
ORDERS = ('query_first', 'unestablished')
QUERY_PLAN_CODES = ('path_unresolved_at_planning', 'prediction_unavailable_pair', 'unrecognized_filter_kind')
LIFECYCLE_LIMITATIONS = ('attempt:lifecycle_unresolved', 'attempt:lifecycle_conflicting', 'attempt:unsupported',
                         'attempt:not_reached', 'attempt:started_without_result')
LIMITATIONS = frozenset(['query_plan:' + code for code in QUERY_PLAN_CODES] + list(LIFECYCLE_LIMITATIONS))
COMPARISON_KEYS = ('observation', 'observation_basis', 'operation_relation', 'target_relation', 'order', 'limitations')

# Keys no current document carries. A reader that finds one is reading a
# document from another contract; it is rejected at that exact path.
REMOVED_STEP_KEYS = ('drift', 'deny_signal')
REMOVED_COMPARISON_KEYS = ('scope', 'prediction', 'conclusion', 'obligations', 'references')
REMOVED_ATTEMPT_KEYS = ('exit_code', 'syscall_errno', 'native_rc', 'normalized_path')
REMOVED_QUERY_KEYS = ('scope', 'effective_filter_value')
REMOVED_REPLY_KEYS = ('deny_signal_total', 'comparison_conditions')
REMOVED_DATA_KEYS = ('runner_startup_diagnostics', 'policy_augmentation', 'app_provenance', 'runner_provenance',
                     'request_path', 'runner_service_bundle_id', 'runner_service_name', 'runner_registry_id',
                     'runner_service_executable', 'error', 'log_last')
REMOVED_DIAGNOSTIC_KEYS = ('worker_pid', 'capture_status', 'first_deny')
SPECIMEN_KEYS = ('request_path', 'policy', 'host', 'runner_provenance', 'app_provenance', 'binaries')
AUGMENTATION_STATUSES = ('not_requested', 'applied', 'failed', 'not_applicable')
IMPORT_STATUSES = ('complete', 'incomplete', 'failed', 'not_applicable')

# Attempt-to-query mapping: the operation and filter kind a completed attempt corresponds to.
ATTEMPT_OPERATIONS = {
    ('file', 'open_read'): ('file-read-data', 'path'), ('file', 'access'): ('file-read-data', 'path'),
    ('file', 'open_write'): ('file-write-data', 'path'), ('file', 'unlink'): ('file-write-unlink', 'path'),
    ('mach_lookup', 'bootstrap_look_up'): ('mach-lookup', 'global_name'),
    ('sysctl', 'read'): ('sysctl-read', 'sysctl_name'), ('exec', 'spawn'): ('process-exec*', 'path'),
    ('file', 'create'): (None, 'path'),
}
PERMISSION_ERRNOS = (1, 13)
PERMISSION_OUTCOMES = ('open_failed', 'unlink_failed', 'access_failed', 'sysctl_failed', 'exec_failed')

PATH_FORMS = ('realpath_resolved', 'firmlink_resolved')
ATTEMPT_PATH_FORMS = ('realpath_resolved', 'parent_realpath_resolved')


# ---------------------------------------------------------------------------
# Version gate
# ---------------------------------------------------------------------------

def _version_error(label, value, expected):
    if type(value) is not int:
        return f'malformed {label}: schema_version {value!r} is not an integer'
    if value != expected:
        return f'unsupported {label}: schema_version {value} (this reader accepts {expected})'
    return None


def is_envelope(document):
    """A controller envelope carries `kind` and `data`; a bare reply carries `steps`."""
    return isinstance(document, dict) and 'data' in document and 'steps' not in document


def version_errors(document):
    """One error for the first unsupported or malformed version, else []."""
    if not isinstance(document, dict):
        return ['document is not an object']
    if is_envelope(document):
        error = _version_error('controller envelope', document.get('schema_version'), contract.CONTROLLER_ENVELOPE)
        if error:
            return [error]
        data = document.get('data')
        runner = data.get('runner_result') if isinstance(data, dict) else None
        if runner is None:
            return []
        if not isinstance(runner, dict):
            return ['malformed runner reply: data.runner_result is not an object']
        error = _version_error('runner response', runner.get('schema_version'), contract.RESPONSE_SCHEMA)
        return [error] if error else []
    error = _version_error('runner response', document.get('schema_version'), contract.RESPONSE_SCHEMA)
    return [error] if error else []


def _reply(document):
    """The runner reply of a supported document, or None when the envelope has no reply."""
    if is_envelope(document):
        data = document.get('data') or {}
        return data.get('runner_result')
    return document


def _gate(document):
    errors = version_errors(document)
    if errors:
        raise ValueError(errors[0])


# ---------------------------------------------------------------------------
# Path forms
# ---------------------------------------------------------------------------

def validate_path_diagnostics(path, *, forms=PATH_FORMS):
    """Validate the compact three-state representation without inferring resolution."""
    if not isinstance(path, dict) or not isinstance(path.get('input'), str):
        return ['path diagnostics require a string input']
    if 'same_as_input' not in path:
        return ['path diagnostics require same_as_input']
    same = path.get('same_as_input')
    if not isinstance(same, list) or any(not isinstance(x, str) for x in same) or \
            len(set(same)) != len(same) or any(x not in forms for x in same):
        return ['same_as_input must contain unique supported form names']
    errors = []
    for name in forms:
        if (name in same) == (name in path):
            errors.append(f'{name} must be either listed in same_as_input or present, exclusively')
        if name in path and path[name] is not None:
            if not isinstance(path[name], str):
                errors.append(f'{name} must be a string or null')
            elif path[name] == path['input']:
                errors.append(f'{name} with identical UTF-8 bytes must be listed in same_as_input')
    return errors


def path_form(path, name, forms=PATH_FORMS):
    """'same_as_input', 'resolved', 'unavailable' or 'invalid' for one host path form."""
    if validate_path_diagnostics(path, forms=forms):
        return 'invalid'
    if name in path.get('same_as_input', []):
        return 'same_as_input'
    return 'unavailable' if path.get(name) is None else 'resolved'


# ---------------------------------------------------------------------------
# Step-level derivations from raw fields (classification tables, not verdicts)
# ---------------------------------------------------------------------------

def query_column(step):
    """The query channel's answer: allow or deny from a validator record, else unavailable."""
    query = step.get('sandbox_check') if isinstance(step, dict) else None
    if isinstance(query, dict) and query.get('result_source') == 'validator' and query.get('outcome') in ('allow', 'deny'):
        return query['outcome']
    return 'unavailable'


def expected_observation(attempt):
    """(observation, basis) the attempt channel's raw fields support."""
    if not isinstance(attempt, dict) or attempt.get('result_source') != 'worker':
        return ('unavailable', 'no_completed_worker_result')
    rc, outcome, errno = attempt.get('rc'), attempt.get('outcome'), attempt.get('errno')
    if attempt.get('requested_kind') == 'exec' and type(attempt.get('child_pid')) is int and attempt['child_pid'] > 0:
        return ('succeeded', 'spawned_child')
    if outcome == 'ok' and rc == 0:
        return ('succeeded', 'completed_worker_status')
    if type(rc) is int and rc != 0:
        if outcome in PERMISSION_OUTCOMES and errno in PERMISSION_ERRNOS:
            return ('permission_failure', 'permission_errno')
        if outcome == 'lookup_failed' and attempt.get('error') == 'bootstrap_look_up: kr=1100':
            return ('permission_failure', 'bootstrap_permission_result')
        return ('other_failure', 'completed_worker_status')
    return ('unavailable', 'no_completed_worker_result')


def expected_relations(query, attempt):
    """(operation_relation, target_relation) from the submitted operations and targets."""
    mapping = ATTEMPT_OPERATIONS.get((attempt.get('requested_kind'), attempt.get('requested_action')))
    operation, filter_kind = mapping if mapping else (None, None)
    query_operation = query.get('operation') if isinstance(query.get('operation'), str) else ''
    broad = '*' in query_operation and not (operation == 'process-exec*' and query_operation == operation)
    if operation is None or broad:
        operation_relation = 'unresolved'
    else:
        operation_relation = 'matched' if operation == query_operation else 'different'
    if filter_kind is None or query.get('filter_kind') != filter_kind or \
            query.get('filter_value') is None or attempt.get('requested_path') is None:
        target_relation = 'unresolved'
    else:
        target_relation = 'same_submitted' if query['filter_value'] == attempt['requested_path'] else 'different_submitted'
    return operation_relation, target_relation


def _ordering_chain(runner):
    worker = runner.get('runner_subprocess')
    ordering = worker.get('ordering') if isinstance(worker, dict) else None
    if not isinstance(ordering, dict):
        return False
    return all(ordering.get(k) is True for k in ('collection_closed_before_proceed', 'proceed_set', 'proceed_observed',
                                                   'worker_lifetime_established')) \
        and ordering.get('protocol_violations') == [] and runner.get('sandboxed_after_apply') is True


def eligible_order(runner, step):
    """True when the step's native record and the run's chain support query_first."""
    query = step.get('sandbox_check') or {}
    worker = runner.get('runner_subprocess') or {}
    validator = runner.get('validator_subprocess') or {}
    rc, err = query.get('native_rc'), query.get('errno')
    native = type(rc) is int and type(err) is int and query.get('rc') == rc and (
        (query.get('outcome') == 'allow' and rc == 0) or (query.get('outcome') == 'deny' and rc == 1 and err == 0))
    records = validator.get('records') or []
    matches = [r for r in records if isinstance(r, dict) and r.get('step_id') == step.get('step_id')]
    associated = len(matches) == 1 and all(matches[0].get(k) == v for k, v in {
        'operation': query.get('operation'), 'filter_type': str(query.get('filter_kind')).upper(),
        'filter_value': None if query.get('filter_kind') == 'none' else query.get('filter_value'),
        'outcome': query.get('outcome'), 'rc': rc, 'errno': err}.items())
    return _ordering_chain(runner) and query.get('result_source') == 'validator' and native and associated \
        and isinstance(worker, dict) and query.get('pid') == worker.get('pid')


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_step(runner, step, failed_reporting):
    errors = []
    sid = step.get('step_id')
    for key in REMOVED_STEP_KEYS:
        if key in step:
            errors.append(f'{sid}: removed key steps[].{key}')
    query = step.get('sandbox_check')
    attempt = step.get('attempt')
    if not isinstance(query, dict):
        errors.append(f'{sid}: missing sandbox_check')
        query = {}
    if not isinstance(attempt, dict):
        errors.append(f'{sid}: missing attempt')
        attempt = {}
    for key in REMOVED_QUERY_KEYS:
        if key in query:
            errors.append(f'{sid}: removed key sandbox_check.{key}')
    for key in REMOVED_ATTEMPT_KEYS:
        if key in attempt:
            errors.append(f'{sid}: removed key attempt.{key}')
    for key in ('requested_kind', 'requested_action'):
        if not isinstance(attempt.get(key), str):
            errors.append(f'{sid}: missing attempt.{key}')
    if type(attempt.get('rc')) is not int:
        errors.append(f'{sid}: invalid attempt.rc')
    if attempt.get('errno') is not None and type(attempt.get('errno')) is not int:
        errors.append(f'{sid}: invalid attempt.errno')
    if not isinstance(query.get('operation'), str) or not isinstance(query.get('filter_kind'), str):
        errors.append(f'{sid}: missing sandbox_check.operation or filter_kind')
    if query.get('outcome') == 'prediction_unavailable' and query.get('rc') != -1:
        errors.append(f'{sid}: unavailable prediction requires rc=-1')
    path = query.get('path_diagnostics')
    if path is not None:
        if not isinstance(path, dict) or (path.get('observer'), path.get('phase')) != ('runner_host', 'after_orchestration'):
            errors.append(f'{sid}: path diagnostics lack host/phase provenance')
        errors.extend(f'{sid}: {error}' for error in validate_path_diagnostics(path))
    attempt_path = attempt.get('path_diagnostics')
    if attempt_path is not None:
        if not isinstance(attempt_path, dict) or \
                (attempt_path.get('observer'), attempt_path.get('phase')) != ('runner_host', 'after_orchestration'):
            errors.append(f'{sid}: attempt path diagnostics lack host/phase provenance')
        if isinstance(attempt_path, dict):
            if attempt_path.get('input') != attempt.get('requested_path') or not isinstance(attempt.get('requested_path'), str):
                errors.append(f'{sid}: attempt path diagnostics input differs from requested_path')
            errors.extend(f'{sid}: attempt {error}' for error in validate_path_diagnostics(attempt_path, forms=ATTEMPT_PATH_FORMS))
    elif attempt.get('requested_kind') in ('file', 'exec') and isinstance(attempt.get('requested_path'), str) and attempt['requested_path']:
        errors.append(f'{sid}: file/exec attempt without path diagnostics')
    comparison = step.get('comparison')
    if failed_reporting:
        if comparison is not None:
            errors.append(f'{sid}: reporting failure must withhold every comparison')
        return errors
    if not isinstance(comparison, dict):
        errors.append(f'{sid}: missing comparison')
        return errors
    for key in REMOVED_COMPARISON_KEYS:
        if key in comparison:
            errors.append(f'{sid}: removed key comparison.{key}')
    if set(comparison) - set(COMPARISON_KEYS) - set(REMOVED_COMPARISON_KEYS):
        errors.append(f'{sid}: unknown comparison keys {sorted(set(comparison) - set(COMPARISON_KEYS))}')
    for key, allowed in (('observation', OBSERVATIONS), ('observation_basis', OBSERVATION_BASES),
                         ('operation_relation', OPERATION_RELATIONS), ('target_relation', TARGET_RELATIONS),
                         ('order', ORDERS)):
        if comparison.get(key) not in allowed:
            errors.append(f'{sid}: invalid comparison.{key}')
    limits = comparison.get('limitations')
    if not isinstance(limits, list) or any(not isinstance(x, str) for x in limits):
        errors.append(f'{sid}: invalid comparison.limitations')
        limits = []
    for limit in limits:
        if limit not in LIMITATIONS:
            errors.append(f'{sid}: limitation outside the vocabulary: {limit}')
    if len(set(limits)) != len(limits):
        errors.append(f'{sid}: repeated limitation')
    # Classification checks against the raw channel fields.
    observation, basis = expected_observation(attempt)
    if (comparison.get('observation'), comparison.get('observation_basis')) != (observation, basis):
        errors.append(f'{sid}: comparison.observation {comparison.get("observation")}/{comparison.get("observation_basis")} '
                      f'disagrees with the attempt fields ({observation}/{basis})')
    operation_relation, target_relation = expected_relations(query, attempt)
    if comparison.get('operation_relation') != operation_relation:
        errors.append(f'{sid}: comparison.operation_relation disagrees with the submitted operations ({operation_relation})')
    if comparison.get('target_relation') != target_relation:
        errors.append(f'{sid}: comparison.target_relation disagrees with the submitted targets ({target_relation})')
    eligible = eligible_order(runner, step)
    if comparison.get('order') == 'query_first' and not eligible:
        errors.append(f'{sid}: query_first lacks eligible record or ordering chain')
    if comparison.get('order') == 'unestablished' and eligible:
        errors.append(f'{sid}: eligible record with complete chain requires query_first')
    plan_limits = [l for l in limits if l.startswith('query_plan:')]
    if query.get('outcome') == 'prediction_unavailable':
        if query.get('result_source') != 'synthetic' or query.get('missing_reason') != 'query_not_requested':
            errors.append(f'{sid}: planning exclusion requires a synthetic query_not_requested record')
        if len(plan_limits) != 1:
            errors.append(f'{sid}: planning exclusion requires exactly one query_plan limitation')
    elif plan_limits:
        errors.append(f'{sid}: query_plan limitation without a planning exclusion')
    summary = (attempt.get('lifecycle') or {}).get('summary') if isinstance(attempt.get('lifecycle'), dict) else None
    expected_lifecycle = lifecycle_contract.LIMITATION_FOR_SUMMARY.get(summary) if summary else None
    lifecycle_limits = [l for l in limits if l.startswith('attempt:')]
    if lifecycle_limits != ([expected_lifecycle] if expected_lifecycle else []):
        errors.append(f'{sid}: lifecycle limitations {lifecycle_limits} disagree with attempt.lifecycle.summary {summary!r}')
    return errors


def _validate_reply(runner):
    errors = []
    for key in REMOVED_REPLY_KEYS:
        if key in runner:
            errors.append(f'removed key {key}')
    failure = runner.get('reporting_failure')
    failed_reporting = failure is not None
    if failed_reporting or runner.get('normalized_outcome') == 'runner_reporting_failed':
        if runner.get('normalized_outcome') != 'runner_reporting_failed' or runner.get('rc') != 1 or \
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
        if not isinstance(spawn, dict) or spawn.get('origin') != 'runner_host' or spawn.get('operation') != 'posix_spawn' or \
                not isinstance(spawn.get('executable_path'), str) or not spawn['executable_path'] or \
                type(spawn.get('return_code')) is not int or spawn['return_code'] == 0 or \
                not isinstance(spawn.get('diagnostic'), str):
            errors.append('invalid validator_spawn_failure record')
        elif runner.get('validator_subprocess') is not None:
            errors.append('validator_spawn_failure cannot coexist with a validator subprocess')
    steps_value = runner.get('steps')
    if not isinstance(steps_value, list):
        errors.append('steps is not a list')
        steps_value = []
    for step in steps_value:
        if not isinstance(step, dict):
            errors.append('step is not an object')
            continue
        errors.extend(_validate_step(runner, step, failed_reporting))
    if not failed_reporting:
        errors.extend(_validate_ordering(runner))
    sub = runner.get('runner_subprocess')
    if isinstance(sub, dict) and not failed_reporting and sub.get(lifecycle_contract.RECORD_KEY) is None:
        errors.append('worker subprocess without runner_subprocess.disposition')
    return errors


def _validate_ordering(runner):
    errors = []
    worker = runner.get('runner_subprocess')
    validator = runner.get('validator_subprocess') or {}
    if not isinstance(worker, dict):
        return errors
    ordering = worker.get('ordering')
    if not isinstance(ordering, dict):
        return ['runner_subprocess.ordering is required beside a worker subprocess']
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
    if s and not c:
        contradictions.append('release_without_collection_closure')
    if o and not s:
        contradictions.append('acknowledgement_without_release')
    if (s or o) and runner.get('sandboxed_after_apply') is not True:
        contradictions.append('release_without_successful_application')
    failure = ((worker.get('worker_evidence') or {}).get('failure') or {})
    if failure.get('operation') == 11 and (o or any((x.get('attempt') or {}).get('result_source') == 'worker'
                                                     for x in runner.get('steps', []) if isinstance(x, dict))):
        contradictions.append('attempt_or_acknowledgement_after_proceed_failure')
    for fault in contradictions:
        if fault not in faults:
            errors.append('unmarked ordering protocol violation: ' + fault)
    if c != (disposition != 'not_invoked'):
        errors.append('ordering collection decision disagrees with validator disposition')
    if disposition == 'reaped' and validator.get('reaped') is not True:
        errors.append('ordering reaped disposition lacks validator reap evidence')
    if disposition == 'unconfirmed' and (not validator or validator.get('reaped') is not False):
        errors.append('ordering unconfirmed disposition lacks validator evidence')
    if disposition in {'not_needed', 'not_spawned', 'not_invoked'} and validator:
        errors.append('ordering terminal decision contradicts validator subprocess')
    return errors


def _validate_envelope(document):
    errors = []
    data = document.get('data')
    if not isinstance(data, dict):
        return ['data is not an object']
    for key in REMOVED_DATA_KEYS:
        if key in data:
            errors.append(f'removed key data.{key}')
    specimen = data.get('specimen')
    if not isinstance(specimen, dict):
        errors.append('missing data.specimen')
    else:
        for key in SPECIMEN_KEYS:
            if key not in specimen:
                errors.append(f'missing data.specimen.{key}')
        policy = specimen.get('policy')
        if not isinstance(policy, dict):
            errors.append('data.specimen.policy is not an object')
        else:
            augmentation = policy.get('augmentation')
            if not isinstance(augmentation, dict) or augmentation.get('status') not in AUGMENTATION_STATUSES or \
                    not isinstance(augmentation.get('applied'), list):
                errors.append('invalid data.specimen.policy.augmentation')
            imports = policy.get('imports')
            if not isinstance(imports, dict) or imports.get('status') not in IMPORT_STATUSES or \
                    not isinstance(imports.get('records'), list):
                errors.append('invalid data.specimen.policy.imports')
            elif imports['status'] in ('failed', 'not_applicable') and (imports.get('records') or imports.get('closure_sha256') is not None):
                errors.append('an unrun imports scan carries no records or closure hash')
        host = specimen.get('host')
        if not isinstance(host, dict) or any(k not in host for k in ('macos_version', 'macos_build', 'kernel_release', 'arch')):
            errors.append('invalid data.specimen.host')
        binaries = specimen.get('binaries')
        if not isinstance(binaries, dict) or any(k not in binaries for k in ('service', 'worker', 'validator')):
            errors.append('invalid data.specimen.binaries')
        else:
            for role, record in binaries.items():
                if record is None:
                    continue
                if not isinstance(record, dict) or record.get('verification') not in ('match', 'mismatch', 'unavailable') or \
                        (record['verification'] == 'match') != (record.get('reason') is None):
                    errors.append(f'invalid data.specimen.binaries.{role}')
        app = specimen.get('app_provenance')
        if app is not None and (not isinstance(app, dict) or set(app) != {'evidence_manifest_path', 'evidence_verify'}):
            errors.append('data.specimen.app_provenance carries keys other than the manifest path and verify report')
    client = data.get('runner_client')
    if client is not None:
        if not isinstance(client, dict) or 'request_delivery' not in client:
            errors.append('data.runner_client lacks request_delivery')
        else:
            delivery = client['request_delivery']
            if delivery is not None and (not isinstance(delivery, dict) or type(delivery.get('bytes_written')) is not int
                                         or (delivery.get('error') is not None and not isinstance(delivery['error'], str))):
                errors.append('invalid data.runner_client.request_delivery')
    diagnostics = data.get('runner_sandbox_diagnostics')
    if diagnostics is not None:
        if not isinstance(diagnostics, dict):
            errors.append('data.runner_sandbox_diagnostics is not an object')
        else:
            for key in REMOVED_DIAGNOSTIC_KEYS:
                if key in diagnostics:
                    errors.append(f'removed key data.runner_sandbox_diagnostics.{key}')
    return errors


def validate(document):
    """The single version error, or every shape error of a supported document."""
    errors = version_errors(document)
    if errors:
        return errors
    if is_envelope(document):
        errors.extend(_validate_envelope(document))
        runner = _reply(document)
        if runner is not None:
            errors.extend(_validate_reply(runner))
        return errors
    return _validate_reply(document)


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def steps(document):
    """The reply's steps, after the version gate; [] when the envelope has no reply."""
    _gate(document)
    runner = _reply(document)
    if runner is None:
        return []
    value = runner.get('steps')
    return deepcopy(value) if isinstance(value, list) else []


def _lookup(step, path):
    current = step
    for key in path.split('.'):
        if not isinstance(current, dict) or key not in current:
            return ('<absent>',)
        current = current[key]
    return current


def select(steps_value, **fields):
    """Steps whose fields equal the given values.

    Keys name comparison fields directly (`observation`, `operation_relation`,
    `order`, `limitations`, ...), `query` for the query channel's answer
    (allow, deny or unavailable), `step_id`, or any dotted path spelled with
    `__` (`attempt__errno=13`, `sandbox_check__outcome='deny'`). A value of
    `select.ABSENT` matches a missing key; `None` matches an explicit null.
    """
    chosen = []
    for step in steps_value:
        if not isinstance(step, dict):
            continue
        ok = True
        for key, wanted in fields.items():
            if key == 'query':
                got = query_column(step)
            elif key in COMPARISON_KEYS:
                got = _lookup(step, 'comparison.' + key)
            else:
                got = _lookup(step, key.replace('__', '.'))
            if got == ('<absent>',):
                got = ABSENT
            if got != wanted:
                ok = False
                break
        if ok:
            chosen.append(step)
    return chosen


class _Absent:
    def __repr__(self):
        return '<absent>'


ABSENT = _Absent()
select.ABSENT = ABSENT


def lifecycle(document):
    """The registered lifecycle account of a supported document."""
    _gate(document)
    envelope = document if is_envelope(document) else {'data': {'runner_result': document}}
    view = read_lifecycle(envelope)
    return {'reporting': view['reporting'], 'summaries': summaries(view), 'record': view['record'],
            'malformed': view['malformed'],
            'projections': {k: view['projections'].get(k) for k in
                            ('process_disposition', 'termination_cause', 'stop_reason', 'disposition_integrity')}}


def denials(document):
    """The optional log channel with candidate references resolved in place."""
    _gate(document)
    if not is_envelope(document):
        raise ValueError('denial evidence lives in the controller envelope, not the bare reply')
    data = document.get('data') or {}
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
    return deepcopy({
        'capture_status': capture.get('capture_status', 'not_reported') if data.get('sandbox_log_capture') is not None else 'not_reported',
        'correlation_status': diagnostics.get('correlation_status', 'not_reported'),
        'permission_failures_without_record': diagnostics.get('permission_failures_without_record'),
        'window': capture.get('window'), 'events': events, 'candidates': candidates,
        'event_reporting': 'reported' if events is not None else 'not_reported',
        'association_reporting': 'reported' if associations is not None else 'not_reported',
        'diagnostics': data.get('runner_sandbox_diagnostics'),
        'capture': data.get('sandbox_log_capture'),
    })

"""Independent acceptance oracle for the worker disposition record.

The oracle reads raw observations from one envelope, computes the expected
claim for every lifecycle question from the contract's claim tables, and checks
the record's claims, their evidence references and every registered projection
against that expectation. It never calls the production resolver, never trusts
a producer-supplied basis without checking that it resolves, and reports
interpretation (claims), integrity (references and facts), projection (D7) and
transport (D8) findings separately.

Expected answers come from `expected_claims`, a declarative evaluation of the
contract tables over normalized observations. The hand-reviewed rows in
`lifecycle_contract.EXAMPLES` anchor it: `self_check` requires the evaluation
to reproduce every row, requires a record built from each row to be accepted,
and requires deliberate mutations of accepted records to be rejected with the
expected rule. Neither a checker that accepts everything nor one that rejects
everything can pass.

Findings are dicts: {'rule', 'kind', 'question', 'step_index', 'detail'}.
"""
from copy import deepcopy
import itertools

import contract
import lifecycle_contract as C
from lifecycle_adapter import read_lifecycle
from document_versions import version_errors

MISSING = C.MISSING
ORDER = {op: position for position, op in enumerate(C.PROTOCOL_ORDER)}


# ---------------------------------------------------------------------------
# Observations.
# ---------------------------------------------------------------------------

def extract_observations(envelope, view):
    """Normalized raw facts from runner_subprocess plus the record's per-step facts."""
    runner = envelope['data']['runner_result']
    sub = runner.get('runner_subprocess') or {}

    def field(name):
        return sub[name] if name in sub and sub[name] is not None else MISSING

    obs = C.observations(
        reaped=sub.get('reaped'), exit_code=sub.get('exit_code'), term_signal=sub.get('term_signal'),
        poll_stop_reason=field('poll_stop_reason'), exit_requested=sub.get('exit_requested'),
        # The host encodes an observed non-request as an absent object once it has
        # recorded the cleanup phase (exit_requested); without that phase recorded,
        # absence is not an observation.
        termination_request=(sub['termination_request'] if 'termination_request' in sub
                             else None if 'exit_requested' in sub else MISSING),
        cleanup_trigger=field('cleanup_trigger'), grace_end=field('grace_end'),
        collection_basis=field('collection_basis'),
        progress=(sub.get('worker_evidence') or {}).get('progress'),
        steps=tuple({'slot': entry['slot'], 'supported': entry['attempt_support'] == 'supported'}
                    for entry in view['steps']))
    for name in ('wait_errors', 'done_observed'):
        obs[name] = sub.get(name, MISSING)
    obs['worker_failure'] = (sub.get('worker_evidence') or {}).get('failure', MISSING)
    return obs


# ---------------------------------------------------------------------------
# Expected claims from the claim tables.
# ---------------------------------------------------------------------------

def supported(answer, value=None):
    claim = {'state': 'supported', 'answer': answer}
    if value is not None:
        claim['value'] = value
    return claim


def unresolved(reason):
    return {'state': 'unresolved', 'reason': reason}


def inapplicable(reason):
    return {'state': 'inapplicable', 'reason': reason}


CONFLICTING = {'state': 'conflicting'}


def association(progress, plan_len):
    """(answer or None, protocol position or None). None answer: no word or unrecognized."""
    if progress is None:
        return None, None
    op, phase, index = progress.get('operation'), progress.get('phase'), progress.get('index')
    if op not in C.OPERATIONS or phase not in C.PHASES:
        return 'unrecognized', None
    raw = progress.get('raw')
    if type(raw) is not int or not 0 < raw <= 0xffffffff or raw >> 24 != op \
            or (raw >> 20) & 15 != phase or (raw & 0xfffff) != (index + 1 if type(index) is int else 0):
        return 'invalid', None
    if op in C.INDEXED_OPERATIONS:
        if type(index) is not int or index < 0 or (op == C.OP_ATTEMPT and index >= plan_len):
            return 'invalid', None
        return C.INDEXED_OPERATIONS[op], (ORDER[op], index, phase)
    return ('invalid', None) if index is not None else ('none', (ORDER[op], 0, phase))


def boundary(i):
    return (ORDER[C.OP_ATTEMPT], i, 1)


def after_slot(i):
    return (ORDER[C.OP_ATTEMPT], i, 2)


def expected_claims(obs):
    """Total evaluation of the contract tables; returns (claims, steps, issues)."""
    claims, issues = {}, []
    reaped, exit_code, signal = obs['reaped'], obs['exit_code'], obs['term_signal']
    if reaped is not True:
        claims['final_status'] = unresolved('no_successful_reap')
    elif type(exit_code) is int and type(signal) is int:
        claims['final_status'] = CONFLICTING
        issues.append({'kind': 'conflict', 'rule': 'D1', 'question': 'final_status',
                       'observations': ['exit_code', 'term_signal']})
    elif type(signal) is int:
        claims['final_status'] = supported('signal', signal)
    elif type(exit_code) is int:
        claims['final_status'] = supported('exit_code', exit_code)
    else:
        claims['final_status'] = unresolved('status_unusable')

    stop = obs['poll_stop_reason']
    claims['stop_reason'] = supported(stop) if isinstance(stop, str) and stop != MISSING else unresolved(C.NOT_RECORDED)

    exit_requested = obs['exit_requested']
    for name in ('cleanup_trigger', 'grace_end'):
        raw = obs[name]
        if exit_requested is False:
            claims[name] = inapplicable('exit_not_requested')
        elif isinstance(raw, str) and raw != MISSING:
            claims[name] = supported(raw)
        else:
            claims[name] = unresolved(C.NOT_RECORDED)
    request = obs['termination_request']
    if exit_requested is False:
        claims['kill_request_and_result'] = inapplicable('exit_not_requested')
    elif request is MISSING:
        claims['kill_request_and_result'] = unresolved(C.NOT_RECORDED)
    elif request is None:
        claims['kill_request_and_result'] = supported('none')
    else:
        claims['kill_request_and_result'] = supported('requested', dict(request))

    basis = obs['collection_basis']
    claims['collection_basis'] = supported(basis) if isinstance(basis, str) and basis != MISSING \
        else unresolved(C.NOT_RECORDED)
    terminal = basis == 'after_confirmed_reap' and reaped is True

    plan_len = len(obs['steps'])
    assoc, position = association(obs['progress'], plan_len)
    if obs['progress'] is None:
        claims['progress_association'] = inapplicable('no_progress_word')
    elif assoc == 'unrecognized':
        claims['progress_association'] = unresolved('progress_unrecognized')
    elif assoc in ('step_index', 'parameter_index'):
        claims['progress_association'] = supported(assoc, obs['progress']['index'])
    else:
        claims['progress_association'] = supported(assoc)

    steps = []
    for i, entry in enumerate(obs['steps']):
        slot, is_supported = entry['slot'], entry['supported']
        step = {'step_requested_operation_applicability': supported('supported' if is_supported else 'unsupported')}
        completed = slot == 'completed'
        if position is not None and position < boundary(i) and completed and terminal:
            step['step_boundary_reached'] = CONFLICTING
            issues.append({'kind': 'conflict', 'rule': 'D5', 'question': 'step_boundary_reached', 'step_index': i,
                           'observations': ['progress', 'slot', 'collection_basis']})
        elif (position is not None and position >= boundary(i)) or (completed and is_supported):
            step['step_boundary_reached'] = supported('reached')
        elif position is not None and not completed and terminal:
            step['step_boundary_reached'] = supported('not_reached')
        elif position is not None and not completed:
            step['step_boundary_reached'] = unresolved('basis_not_terminal')
        else:
            step['step_boundary_reached'] = unresolved('no_usable_progress')
        if not is_supported:
            step['step_result_published'] = inapplicable('unsupported_attempt')
        elif slot == 'absent':
            step['step_result_published'] = unresolved('slot_unavailable')
        elif completed:
            step['step_result_published'] = supported('published')
        elif not terminal:
            step['step_result_published'] = unresolved('basis_not_terminal')
        elif position is not None and position >= after_slot(i):
            step['step_result_published'] = CONFLICTING
            issues.append({'kind': 'conflict', 'rule': 'D5', 'question': 'step_result_published', 'step_index': i,
                           'observations': ['progress', 'slot', 'collection_basis']})
        else:
            step['step_result_published'] = supported('unpublished')
        steps.append(step)
    return claims, steps, issues


def expected_projections(claims, steps, obs):
    final = claims['final_status']
    if final['state'] == 'supported':
        disposition = ('signaled' if final['answer'] == 'signal'
                       else 'clean_exit' if final['value'] == 0 else 'nonzero_exit')
    elif final['state'] == 'conflicting':
        disposition = 'conflicting'
    else:
        disposition = 'unconfirmed'
    cause = C.CAUSE_UNKNOWN
    if final['state'] == 'supported' and final['answer'] == 'exit_code' and final['value'] == 0:
        cause = None
    elif final['state'] == 'supported' and final['answer'] == 'signal':
        trigger, grace, kill = claims['cleanup_trigger'], claims['grace_end'], claims['kill_request_and_result']
        if trigger['state'] == 'supported' and trigger['answer'] in C.CAUSE_FOR_TRIGGER \
                and grace['state'] == 'supported' and grace['answer'] == 'exhausted' \
                and kill['state'] == 'supported' and kill['answer'] == 'requested' \
                and kill['value'].get('rc') == 0 and kill['value'].get('signal') == final['value']:
            cause = C.CAUSE_FOR_TRIGGER[trigger['answer']]
    stop = claims['stop_reason']
    summaries = []
    for step in steps:
        boundary_claim, result = step['step_boundary_reached'], step['step_result_published']
        if step['step_requested_operation_applicability'].get('answer') == 'unsupported':
            summaries.append('unsupported')
        elif result['state'] == 'supported' and result['answer'] == 'published':
            summaries.append('completed')
        elif 'conflicting' in (boundary_claim['state'], result['state']):
            summaries.append('conflicting')
        elif result['state'] == 'supported' and boundary_claim['state'] == 'supported':
            summaries.append('started_without_result' if boundary_claim['answer'] == 'reached' else 'not_reached')
        else:
            summaries.append('unresolved')
    return {'process_disposition': disposition, 'termination_cause': cause,
            'stop_reason': stop['answer'] if stop['state'] == 'supported' and stop['answer'] in C.POLL_STOP_REASONS else None,
            'partial_steps': any(e['slot'] != 'completed' for e in obs['steps']),
            'summaries': summaries}


def expected_error_clauses(claims):
    """Lifecycle clauses the error string must contain, rendered from the account."""
    clauses = []
    if claims['stop_reason'].get('answer') == 'sentinel_deadline':
        kill = claims['kill_request_and_result']
        clauses.append(C.DEADLINE_CLAUSE)
        clauses.append(C.KILL_CLAUSE if kill.get('answer') == 'requested' else C.NO_KILL_CLAUSE)
    return clauses


# ---------------------------------------------------------------------------
# Record construction (for expected fixtures and the self-check).
# ---------------------------------------------------------------------------

BASIS = {
    'final_status': {'exit_code': ['reaped', 'exit_code'], 'signal': ['reaped', 'term_signal']},
    'stop_reason': ['poll_stop_reason'],
    'cleanup_trigger': ['cleanup_trigger', 'exit_requested'],
    'grace_end': ['grace_end', 'exit_requested'],
    'kill_request_and_result': {'requested': ['termination_request'], 'none': ['termination_request', 'exit_requested']},
    'collection_basis': ['collection_basis'],
    'progress_association': ['progress', 'plan'],
    'step_requested_operation_applicability': ['attempt_support'],
    'step_boundary_reached': {'reached': ['progress', 'slot', 'attempt_support'],
                              'not_reached': ['progress', 'slot', 'collection_basis']},
    'step_result_published': {'published': ['slot', 'attempt_support'],
                              'unpublished': ['slot', 'collection_basis', 'progress']},
}


def _with_basis(name, claim, issues, obs, entry=None, step_index=None):
    claim = dict(claim)
    if claim['state'] == 'supported':
        table = BASIS[name]
        tokens = table[claim['answer']] if isinstance(table, dict) else table
        # A fixture cites only observations the reply actually carries.
        claim['basis'] = [t for t in tokens if _resolvable(t, obs, entry)]
    elif claim['state'] == 'conflicting':
        claim['issue'] = next(n for n, issue in enumerate(issues)
                              if issue['question'] == name and issue.get('step_index') == step_index)
    return claim


def build_record(claims, steps, issues, step_ids, obs):
    entries = [{'slot': e['slot'], 'attempt_support': 'supported' if e['supported'] else 'unsupported'}
               for e in obs['steps']]
    return {
        'questions': {name: _with_basis(name, claims[name], issues, obs) for name in C.RUN_QUESTIONS},
        'steps': [{'index': i, 'step_id': step_ids[i], 'slot': entries[i]['slot'],
                   'attempt_support': entries[i]['attempt_support'],
                   'questions': {name: _with_basis(name, step[name], issues, obs, entries[i], i)
                                 for name in C.STEP_QUESTIONS}}
                  for i, step in enumerate(steps)],
        'issues': deepcopy(issues),
    }


def build_envelope(obs, schema_version=contract.RESPONSE_SCHEMA, envelope_version=contract.CONTROLLER_ENVELOPE):
    """A contract-valid envelope for normalized observations; a fixture, not a live result."""
    claims, steps, issues = expected_claims(obs)
    projections = expected_projections(claims, steps, obs)
    step_ids = [f'step{i}' for i in range(len(obs['steps']))]
    record = build_record(claims, steps, issues, step_ids, obs)
    sub = {'pid': 4242, 'reaped': obs['reaped'], 'partial_steps': projections['partial_steps'],
           'worker_evidence': {'abi_version': 7, 'failure_publication': 0, 'failure_state': 'absent',
                               'diagnostic': {'state': 0, 'status': 'absent'}}}
    if obs['exit_code'] is not None:
        sub['exit_code'] = obs['exit_code']
    if obs['term_signal'] is not None:
        sub['term_signal'] = obs['term_signal']
    if obs['exit_requested'] is not None:
        sub['exit_requested'] = obs['exit_requested']
    for name in ('poll_stop_reason', 'cleanup_trigger', 'grace_end', 'collection_basis'):
        if obs[name] is not MISSING:
            sub[name] = obs[name]
    if obs['termination_request'] is not MISSING:
        sub['termination_request'] = deepcopy(obs['termination_request'])
    if obs['progress'] is not None:
        sub['worker_evidence']['progress'] = deepcopy(obs['progress'])
    sub[C.RECORD_KEY] = record
    reply_steps = []
    for i, entry in enumerate(obs['steps']):
        summary = projections['summaries'][i]
        completed = entry['slot'] == 'completed' and entry['supported']
        attempt = {'requested_kind': 'file', 'requested_action': 'open_read', 'requested_path': f'/target{i}',
                   'rc': 0 if completed else -1, 'errno': None, 'error': None, 'observed_path': None,
                   'outcome': 'ok' if completed else C.COMPAT_MISSING_OUTCOME,
                   'result_source': 'worker' if completed else 'synthetic',
                   C.STEP_LIFECYCLE_KEY: {'summary': summary,
                                          'boundary': deepcopy(record['steps'][i]['questions']['step_boundary_reached']),
                                          'result': deepcopy(record['steps'][i]['questions']['step_result_published'])}}
        if not completed:
            attempt['missing_reason'] = ('attempt_not_supported' if not entry['supported']
                                         else 'slot_absent' if entry['slot'] == 'absent' else 'slot_incomplete')
        limitations = [] if summary == 'completed' else [C.LIMITATION_FOR_SUMMARY[summary]]
        reply_steps.append({'step_id': step_ids[i], 'attempt': attempt,
                            'sandbox_check': {'operation': 'file-read-data', 'filter_kind': 'path',
                                              'filter_value': f'/target{i}', 'outcome': 'allow', 'rc': 0,
                                              'native_rc': 0, 'errno': 0, 'result_source': 'validator', 'pid': 4242},
                            'comparison': {'observation': 'succeeded' if completed else 'unavailable',
                                           'observation_basis': 'completed_worker_status' if completed
                                           else 'no_completed_worker_result',
                                           'operation_relation': 'matched', 'target_relation': 'same_submitted',
                                           'order': 'unestablished', 'limitations': limitations}})
    clauses = expected_error_clauses(claims)
    error = '; '.join(clauses) if clauses else None
    runner = {'schema_version': schema_version, 'specimen_id': 'constructed', 'rc': 0 if error is None else 1,
              'normalized_outcome': 'runner_timeout' if clauses else 'ok', 'error': error, 'pid': 4242,
              'policy_format': 'sbpl', 'sandboxed_after_apply': True, 'steps': reply_steps, 'runner_subprocess': sub}
    diagnostics = {'process_disposition': projections['process_disposition'],
                   'termination_cause': projections['termination_cause'], 'stop_reason': projections['stop_reason'],
                   'disposition_integrity': 'valid', 'disposition_issues': [],
                   'correlation_status': 'not_attempted', 'permission_failures_without_record': None}
    return {'schema_version': envelope_version, 'kind': 'run', 'result': {'ok': error is None},
            'data': {'runner_result': runner, 'runner_sandbox_diagnostics': diagnostics, 'sandbox_log_capture': None}}


# ---------------------------------------------------------------------------
# Checking.
# ---------------------------------------------------------------------------

def _finding(rule, kind, detail, question=None, step_index=None):
    return {'rule': rule, 'kind': kind, 'question': question, 'step_index': step_index, 'detail': detail}


def _resolvable(token, obs, entry):
    if token in C.STEP_REFERENCES:
        return entry is not None and entry.get(token) is not None
    if token == 'plan':
        return True
    if token in ('reaped', 'exit_code', 'term_signal', 'exit_requested'):
        return obs[token] is not None
    if token == 'termination_request':
        return obs[token] is not MISSING
    if token == 'progress':
        return obs['progress'] is not None
    return obs.get(token, MISSING) not in (MISSING, None)


def sufficient_basis(name, answer, basis):
    """Required references, separate from computing the answer from observations."""
    tokens = set(basis)
    if name == 'step_boundary_reached' and answer == 'reached':
        return 'progress' in tokens or {'slot', 'attempt_support'} <= tokens
    required = {
        ('final_status', 'signal'): {'reaped', 'term_signal'},
        ('final_status', 'exit_code'): {'reaped', 'exit_code'},
        ('kill_request_and_result', 'none'): {'termination_request', 'exit_requested'},
        ('kill_request_and_result', 'requested'): {'termination_request'},
        ('progress_association', 'step_index'): {'progress', 'plan'},
        ('progress_association', 'invalid'): {'progress', 'plan'},
        ('step_boundary_reached', 'not_reached'): {'progress', 'slot', 'collection_basis'},
        ('step_result_published', 'published'): {'slot', 'attempt_support'},
        ('step_result_published', 'unpublished'): {'slot', 'collection_basis'},
    }.get((name, answer), {
        'stop_reason': {'poll_stop_reason'}, 'cleanup_trigger': {'cleanup_trigger', 'exit_requested'},
        'grace_end': {'grace_end', 'exit_requested'}, 'collection_basis': {'collection_basis'},
        'progress_association': {'progress'}, 'step_requested_operation_applicability': {'attempt_support'},
    }.get(name, set()))
    return required <= tokens


def _compare_claim(name, expected, actual, findings, step_index, obs, entry):
    if actual is None:
        findings.append(_finding('D8', 'missing_claim', 'claim absent', name, step_index))
        return
    if not actual['recognized']:
        # A transported future spelling: the interpretation is unresolved for us, but a
        # supported answer we expected must not be replaced by an unknown one.
        if expected['state'] == 'supported' and actual.get('answer') != expected['answer']:
            findings.append(_finding('D7', 'unrecognized_value', f'unrecognized {actual["raw"]!r} where {expected} was supported',
                                     name, step_index))
        return
    if actual['state'] != expected['state']:
        kind = 'forbidden' if actual['state'] == 'supported' else 'required' if expected['state'] == 'supported' else 'wrong_state'
        rule = C.question(name).conflict.rule if expected['state'] == 'conflicting' and C.question(name).conflict else \
            (C.answer(name, expected['answer']).rules[0] if expected['state'] == 'supported' else
             C.answer(name, actual['answer']).rules[0] if actual['state'] == 'supported' and actual.get('answer') in
             {a.value for a in C.question(name).answers} else 'D3')
        findings.append(_finding(rule, kind, f'expected {expected}, record says {actual["state"]}', name, step_index))
        return
    if expected['state'] == 'supported':
        if actual.get('answer') != expected['answer'] or actual.get('value') != expected.get('value'):
            findings.append(_finding(C.answer(name, expected['answer']).rules[0], 'wrong_answer',
                                     f'expected {expected}, record says {actual.get("answer")!r} {actual.get("value")!r}',
                                     name, step_index))
        if not actual['basis']:
            findings.append(_finding('D7', 'missing_basis', 'supported claim without basis', name, step_index))
        elif not sufficient_basis(name, actual.get('answer'), actual['basis']):
            findings.append(_finding('D8', 'insufficient_basis', 'references do not include a sufficient witness set',
                                     name, step_index))
        if name == 'step_boundary_reached' and actual.get('answer') == 'reached':
            _, position = association(obs['progress'], len(obs['steps']))
            progress_proof = position is not None and position >= boundary(step_index) and 'progress' in actual['basis']
            slot_proof = entry['slot'] == 'completed' and entry['attempt_support'] == 'supported' \
                and {'slot', 'attempt_support'} <= set(actual['basis'])
            if not (progress_proof or slot_proof):
                findings.append(_finding('D8', 'insufficient_basis', 'the cited observations do not prove this boundary',
                                         name, step_index))
        for token in actual['basis']:
            if token not in C.REFERENCES or (C.question(name).scope_kind == 'run' and token in C.STEP_REFERENCES):
                findings.append(_finding('D8', 'unknown_reference', f'basis token {token!r}', name, step_index))
            elif not _resolvable(token, obs, entry):
                findings.append(_finding('D8', 'unresolved_reference', f'basis token {token!r} does not resolve',
                                         name, step_index))
    elif expected['state'] in ('unresolved', 'inapplicable'):
        if actual.get('reason') != expected['reason']:
            findings.append(_finding('D3' if expected['state'] == 'unresolved' else 'D7', 'wrong_reason',
                                     f'expected reason {expected["reason"]!r}, record says {actual.get("reason")!r}',
                                     name, step_index))


def check_record(envelope):
    """Findings for one envelope; empty means the record and projections satisfy the contract."""
    errors = version_errors(envelope)
    if errors:
        error = errors[0]
        kind = 'unsupported_version' if error.startswith('unsupported') else 'malformed_version'
        return [_finding('D8', kind, error)]
    view = read_lifecycle(envelope)
    findings = []
    proj = view['projections']
    if view['reporting'] == 'no_runner_reply':
        return findings
    if view['reporting'] == 'no_worker':
        if proj.get('process_disposition') not in (None, 'no_worker'):
            findings.append(_finding('D7', 'invented_worker', f'no worker but disposition {proj["process_disposition"]!r}'))
        return findings
    if view['reporting'] == 'not_reported':
        findings.append(_finding('D8', 'missing_record', 'response carries a worker subprocess without the record'))
        if proj.get('process_disposition') not in (None, 'withheld'):
            findings.append(_finding('D7', 'unwithheld_projection',
                                     f'missing record projected as {proj["process_disposition"]!r} instead of withheld'))
        return findings
    if view['reporting'] == 'malformed':
        for reason in view['malformed']:
            findings.append(_finding('D8', 'malformed_record', reason))
        return findings

    obs = extract_observations(envelope, view)
    if obs['collection_basis'] == 'after_confirmed_reap' and obs['reaped'] is not True:
        findings.append(_finding('D4', 'invalid_collection_basis', 'terminal collection requires a confirmed reap'))
    claims, steps, issues = expected_claims(obs)
    for name in C.RUN_QUESTIONS:
        _compare_claim(name, claims[name], view['questions'].get(name), findings, None, obs, None)
    for extra in set(view['questions']) - set(C.RUN_QUESTIONS):
        findings.append(_finding('D8', 'unknown_question', f'question {extra!r} is not registered', extra))
    runner_steps = envelope['data']['runner_result'].get('steps') or []
    if len(view['steps']) != len(runner_steps):
        findings.append(_finding('D8', 'step_count', f'record has {len(view["steps"])} steps, reply has {len(runner_steps)}'))
    for i, entry in enumerate(view['steps']):
        reply_step = runner_steps[i] if i < len(runner_steps) else {}
        if entry['step_id'] != reply_step.get('step_id'):
            findings.append(_finding('D8', 'step_identity', f'record step_id {entry["step_id"]!r} vs reply {reply_step.get("step_id")!r}',
                                     step_index=i))
        attempt = reply_step.get('attempt') or {}
        completed = entry['slot'] == 'completed' and entry['attempt_support'] == 'supported'
        if (attempt.get('result_source') == 'worker') != completed:
            findings.append(_finding('D6', 'slot_fact_disagrees', 'attempt.result_source disagrees with the record slot facts',
                                     step_index=i))
        expected_reason = (None if completed else 'attempt_not_supported' if entry['attempt_support'] == 'unsupported'
                           else 'slot_absent' if entry['slot'] == 'absent' else 'slot_incomplete')
        if attempt.get('missing_reason') != expected_reason:
            findings.append(_finding('D6', 'missing_reason_disagrees',
                                     f'missing_reason {attempt.get("missing_reason")!r} vs slot facts {expected_reason!r}',
                                     step_index=i))
        for name in C.STEP_QUESTIONS:
            _compare_claim(name, steps[i][name], entry['questions'].get(name), findings, i, obs, entry)
    # A conflict's pointer must reference the issue for this exact question and step.
    for name, actual, index in [(n, c, None) for n, c in view['questions'].items()] + [
            (n, c, i) for i, entry in enumerate(view['steps']) for n, c in entry['questions'].items()]:
        if actual.get('state') == 'conflicting':
            pointer = actual.get('issue')
            issue = view['issues'][pointer] if type(pointer) is int and 0 <= pointer < len(view['issues']) else {}
            if issue.get('question') != name or issue.get('step_index') != index:
                findings.append(_finding('D8', 'invalid_issue_reference', 'conflict pointer does not resolve to its issue', name, index))
    # Issues: every expected conflict must appear with its rule and observations; no extra conflicts.
    actual_issues = view['issues']
    for issue in issues:
        match = [a for a in actual_issues if a.get('rule') == issue['rule'] and a.get('question') == issue['question']
                 and a.get('step_index') == issue.get('step_index')]
        if not match:
            findings.append(_finding(issue['rule'], 'missing_issue', f'conflict not reported: {issue}', issue['question'],
                                     issue.get('step_index')))
        elif not set(issue['observations']) <= set(match[0].get('observations') or []):
            findings.append(_finding(issue['rule'], 'issue_observations', f'issue lacks observations {issue["observations"]}',
                                     issue['question'], issue.get('step_index')))
    if len(actual_issues) > len(issues):
        findings.append(_finding('D5', 'extra_issue', f'{len(actual_issues) - len(issues)} unexpected issue(s)'))
    # Projections (D7).
    expected = expected_projections(claims, steps, obs)
    if proj.get('partial_steps') is not None and proj['partial_steps'] != expected['partial_steps']:
        findings.append(_finding('D7', 'partial_steps', f'partial_steps {proj["partial_steps"]!r}, expected {expected["partial_steps"]!r}'))
    for i, summary in enumerate(expected['summaries']):
        lifecycle = proj['step_lifecycle'][i] if i < len(proj['step_lifecycle']) else None
        actual_summary = lifecycle.get('summary') if isinstance(lifecycle, dict) else None
        if isinstance(lifecycle, dict):
            for key, question in [('boundary', 'step_boundary_reached'), ('result', 'step_result_published')]:
                if lifecycle.get(key) != view['steps'][i]['questions'][question]['raw']:
                    findings.append(_finding('D7', 'lifecycle_copy', f'{key} differs from its record claim', step_index=i))
        if actual_summary is None:
            findings.append(_finding('D7', 'missing_lifecycle', 'attempt.lifecycle absent', step_index=i))
        elif actual_summary != summary:
            if actual_summary in C.LIFECYCLE_SUMMARIES:
                findings.append(_finding('D7', 'summary', f'lifecycle summary {actual_summary!r}, expected {summary!r}', step_index=i))
            else:
                findings.append(_finding('D7', 'unrecognized_value', f'lifecycle summary {actual_summary!r}', step_index=i))
        limits = proj['step_limitations'][i] if i < len(proj['step_limitations']) else []
        required = C.LIMITATION_FOR_SUMMARY.get(summary)
        runner = envelope['data']['runner_result']
        withheld_comparison = runner.get('normalized_outcome') == 'runner_reporting_failed' \
            and isinstance(runner.get('reporting_failure'), dict) and runner_steps[i].get('comparison') is None
        if required and required not in limits and not withheld_comparison:
            findings.append(_finding('D7', 'limitation', f'comparison lacks {required}', step_index=i))
        for present in limits:
            if present in C.LIMITATION_FOR_SUMMARY.values() and present != required:
                findings.append(_finding('D7', 'limitation', f'comparison carries {present} for summary {summary!r}', step_index=i))
    if proj.get('process_disposition') is not None:
        integrity = proj.get('disposition_integrity')
        if integrity == 'invalid':
            if proj.get('process_disposition') != 'withheld' or proj.get('termination_cause') != C.CAUSE_UNKNOWN:
                findings.append(_finding('D7', 'withholding', 'invalid record must withhold disposition and cause'))
            if not proj.get('disposition_issues'):
                findings.append(_finding('D7', 'withholding', 'invalid record without disposition_issues'))
        else:
            if integrity != 'valid':
                findings.append(_finding('D7', 'integrity', f'disposition_integrity {integrity!r} on a valid record'))
            for key in ('process_disposition', 'termination_cause', 'stop_reason'):
                if proj.get(key) != expected[key]:
                    findings.append(_finding('D7', key, f'{key} {proj.get(key)!r}, expected {expected[key]!r}'))
    runner = envelope['data']['runner_result']
    failure = runner.get('reporting_failure') or {}
    error = failure.get('original_error') if runner.get('normalized_outcome') == 'runner_reporting_failed' else proj.get('error')
    error = error or ''
    outcome = failure.get('original_normalized_outcome', runner.get('normalized_outcome'))
    # Higher-priority worker/setup failures own their error text. The timeout
    # branch renders these clauses; a degraded reply retains that original text.
    for clause in expected_error_clauses(claims) if outcome == 'runner_timeout' else []:
        if clause not in error:
            findings.append(_finding('D7', 'error_clause', f'error lacks {clause!r}'))
    if claims['kill_request_and_result'].get('answer') == 'none' and C.KILL_CLAUSE in error:
        findings.append(_finding('D7', 'error_clause', 'error claims a SIGKILL request the account does not carry'))
    return findings


# ---------------------------------------------------------------------------
# The finite model and the self-check.
# ---------------------------------------------------------------------------

STATUS_AXIS = {
    'unreaped': dict(reaped=False),
    'exit_0': dict(reaped=True, exit_code=0),
    'exit_17': dict(reaped=True, exit_code=17),
    'signal_9': dict(reaped=True, term_signal=9),
    'exit_0_and_signal_9': dict(reaped=True, exit_code=0, term_signal=9),
}
INTERVENTION_AXIS = {
    'done_no_request': dict(poll_stop_reason='done', cleanup_trigger='completion', grace_end='reaped_during_grace',
                            termination_request=None),
    'deadline_no_request': dict(poll_stop_reason='sentinel_deadline', cleanup_trigger='deadline_expiry',
                                grace_end='reaped_during_grace', termination_request=None),
    'deadline_kill_ok': dict(poll_stop_reason='sentinel_deadline', cleanup_trigger='deadline_expiry',
                             grace_end='exhausted', termination_request={'signal': 9, 'rc': 0}),
    'deadline_kill_eperm': dict(poll_stop_reason='sentinel_deadline', cleanup_trigger='deadline_expiry',
                                grace_end='exhausted', termination_request={'signal': 9, 'rc': -1, 'errno': 1}),
    'wait_error_no_request': dict(poll_stop_reason='wait_error', cleanup_trigger='poll_wait_error',
                                  grace_end='wait_error', termination_request=None),
    'policy_write_error': dict(poll_stop_reason='policy_write_error', cleanup_trigger='policy_transfer_error',
                               grace_end='exhausted', termination_request={'signal': 9, 'rc': 0}),
}
PROGRESS_AXIS = {
    'absent': None, 'apply_started': C.progress(8, 1), 'attempt_0_started': C.progress(9, 1, 0),
    'attempt_1_started': C.progress(9, 1, 1), 'attempt_1_returned': C.progress(9, 2, 1),
    'finished_returned': C.progress(10, 2), 'operation_200': C.progress(200, 1, 0),
    'attempt_2_started': C.progress(9, 1, 2),
}
SLOT_AXIS = {
    'none_completed': (C.step('incomplete'), C.step('incomplete')),
    'first_completed': (C.step('completed'), C.step('incomplete')),
    'both_completed': (C.step('completed'), C.step('completed')),
    'second_unsupported_completed': (C.step('completed'), C.step('completed', supported=False)),
}
BASIS_AXIS = tuple(C.COLLECTION_BASES)


def enumerate_model():
    """Every core D-model row as (labels, observations)."""
    for status, intervention, prog, slots, basis in itertools.product(
            STATUS_AXIS, INTERVENTION_AXIS, PROGRESS_AXIS, SLOT_AXIS, BASIS_AXIS):
        obs = C.observations(exit_requested=True, collection_basis=basis, progress=PROGRESS_AXIS[prog],
                             steps=SLOT_AXIS[slots], **STATUS_AXIS[status], **INTERVENTION_AXIS[intervention])
        yield (status, intervention, prog, slots, basis), obs


def _mutations(example):
    """Deliberately wrong outputs, each with the rule expected to reject it."""
    envelope = build_envelope(example.observations)
    runner = envelope['data']['runner_result']
    sub = runner['runner_subprocess']
    record = sub[C.RECORD_KEY]
    diagnostics = envelope['data']['runner_sandbox_diagnostics']

    def mutate(name, rule, change):
        copy = deepcopy(envelope)
        change(copy, copy['data']['runner_result'], copy['data']['runner_result']['runner_subprocess'],
               copy['data']['runner_result']['runner_subprocess'][C.RECORD_KEY], copy['data']['runner_sandbox_diagnostics'])
        return name, rule, copy

    out = []
    def unknown_state(e, r, s, rec, d):
        rec['questions']['stop_reason']['state'] = 'future_state'
    out.append(mutate('unknown_claim_state', 'D8', unknown_state))
    for bad_basis in ([17], [{}], 'reaped', ['exit_requested']):
        def malformed_basis(e, r, s, rec, d, bad_basis=bad_basis):
            rec['questions']['final_status']['basis'] = bad_basis
        if record['questions']['final_status']['state'] == 'supported':
            out.append(mutate('malformed_or_insufficient_basis', 'D8', malformed_basis))
    if runner['steps']:
        def wrong_copy(e, r, s, rec, d):
            r['steps'][0]['attempt'][C.STEP_LIFECYCLE_KEY]['boundary'] = {'state': 'unresolved', 'reason': 'invented'}
        out.append(mutate('lifecycle_copy_disagrees', 'D7', wrong_copy))
    if record['issues']:
        def dangling_issue(e, r, s, rec, d):
            for q in list(rec['questions'].values()) + [q for step in rec['steps'] for q in step['questions'].values()]:
                if q['state'] == 'conflicting':
                    q['issue'] = 99
        out.append(mutate('dangling_issue_reference', 'D8', dangling_issue))
    if sub.get('termination_request') and diagnostics['termination_cause'] in C.CAUSE_LABELS:
        def drop_request(e, r, s, rec, d):
            del s['termination_request']
        out.append(mutate('cause_without_request', 'D2', drop_request))

        def unknown_cause(e, r, s, rec, d):
            d['termination_cause'] = C.CAUSE_UNKNOWN
        out.append(mutate('supported_cause_replaced_by_unknown', 'D7', unknown_cause))
    if 'term_signal' in sub and 'exit_code' not in sub:
        def add_exit(e, r, s, rec, d):
            s['exit_code'] = 0
        out.append(mutate('exit_beside_signal_without_conflict', 'D1', add_exit))
    if record['questions']['final_status']['state'] == 'supported':
        def swap_status(e, r, s, rec, d):
            q = rec['questions']['final_status']
            q['answer'] = 'signal' if q['answer'] == 'exit_code' else 'exit_code'
        out.append(mutate('swapped_final_status', 'D1', swap_status))
    if record['questions']['stop_reason']['state'] == 'supported':
        def wrong_stop(e, r, s, rec, d):
            q = rec['questions']['stop_reason']
            q['answer'] = 'done' if q['answer'] != 'done' else 'child_reaped'
        out.append(mutate('wrong_stop_reason', 'D2', wrong_stop))
    summaries = [a['attempt'][C.STEP_LIFECYCLE_KEY]['summary'] for a in runner['steps']]
    if 'started_without_result' in summaries and 'not_reached' in summaries:
        i, j = summaries.index('started_without_result'), summaries.index('not_reached')

        def swap_steps(e, r, s, rec, d):
            a, b = rec['steps'][i]['questions']['step_boundary_reached'], rec['steps'][j]['questions']['step_boundary_reached']
            rec['steps'][i]['questions']['step_boundary_reached'], rec['steps'][j]['questions']['step_boundary_reached'] = b, a
        out.append(mutate('swapped_step_answers', 'D3', swap_steps))

        def blanket_unresolved(e, r, s, rec, d):
            for k in (i, j):
                rec['steps'][k]['questions']['step_boundary_reached'] = {'state': 'unresolved', 'reason': 'no_usable_progress'}
        out.append(mutate('blanket_unresolved_steps', 'D3', blanket_unresolved))
    if any(a['attempt'][C.STEP_LIFECYCLE_KEY]['summary'] == 'not_reached' for a in runner['steps']):
        k = summaries.index('not_reached')

        def live_not_reached(e, r, s, rec, d):
            s['collection_basis'] = 'execution_may_continue'
            rec['questions']['collection_basis']['answer'] = 'execution_may_continue'
        out.append(mutate('not_reached_under_live_basis', 'D4', live_not_reached))
    for k, step in enumerate(runner['steps']):
        if step['attempt'][C.STEP_LIFECYCLE_KEY]['summary'] == 'completed':
            def drop_limitation_mismatch(e, r, s, rec, d, k=k):
                r['steps'][k]['comparison']['limitations'].append('attempt:not_reached')
            out.append(mutate('lifecycle_limitation_on_completed_step', 'D7', drop_limitation_mismatch))
            break
    if record['issues']:
        def resolve_conflict_silently(e, r, s, rec, d):
            # The producer picks one side of the incompatible observations and drops the issue.
            rec['issues'] = []
            for name, q in rec['questions'].items():
                if q['state'] == 'conflicting':
                    rec['questions'][name] = {'state': 'supported', 'answer': 'signal', 'value': s.get('term_signal'),
                                              'basis': ['reaped', 'term_signal']}
            for st in rec['steps']:
                for name, q in st['questions'].items():
                    if q['state'] == 'conflicting':
                        st['questions'][name] = {'state': 'supported', 'answer': 'unpublished',
                                                 'basis': ['slot', 'collection_basis', 'progress']}
        out.append(mutate('conflict_resolved_silently', record['issues'][0]['rule'], resolve_conflict_silently))

    def wrong_disposition(e, r, s, rec, d):
        d['process_disposition'] = 'clean_exit' if d['process_disposition'] != 'clean_exit' else 'signaled'
    out.append(mutate('wrong_process_disposition', 'D7', wrong_disposition))

    def dangling_basis(e, r, s, rec, d):
        rec['questions']['stop_reason']['basis'] = ['nonexistent']
    if record['questions']['stop_reason']['state'] == 'supported':
        out.append(mutate('unknown_basis_token', 'D8', dangling_basis))

    def missing_record(e, r, s, rec, d):
        del s[C.RECORD_KEY]
    out.append(mutate('record_missing_at_new_version', 'D8', missing_record))
    return out


def _property_checks():
    """D-props over the claim tables: evidence changes affect only dependent claims."""
    checked = 0
    for labels, obs in enumerate_model():
        claims, steps, issues = expected_claims(obs)
        # Removing the progress word removes only progress-based certainty: a completed
        # supported slot keeps its reached boundary and published result.
        without = dict(obs, progress=None)
        claims2, steps2, _ = expected_claims(without)
        for i, entry in enumerate(obs['steps']):
            if entry['slot'] == 'completed' and entry['supported']:
                assert steps2[i]['step_boundary_reached'] == supported('reached'), (labels, i)
                assert steps2[i]['step_result_published'] == supported('published'), (labels, i)
            assert steps2[i]['step_result_published']['state'] != 'conflicting', (labels, i)
        assert claims2['final_status'] == claims['final_status'] and claims2['stop_reason'] == claims['stop_reason']
        # Completing an incomplete supported slot changes that step and partial_steps only.
        for i, entry in enumerate(obs['steps']):
            if entry['slot'] == 'incomplete' and entry['supported']:
                completed = dict(obs, steps=tuple(dict(e, slot='completed') if k == i else e
                                                  for k, e in enumerate(obs['steps'])))
                claims3, steps3, _ = expected_claims(completed)
                assert steps3[i]['step_result_published'] == supported('published'), (labels, i)
                assert claims3 == claims, (labels, i)
                for k in range(len(steps)):
                    if k != i:
                        assert steps3[k] == steps[k], (labels, i, k)
        # An unrelated value change (a different nonzero exit code) touches final_status only.
        if obs['exit_code'] not in (None, 0) and obs['term_signal'] is None:
            claims4, steps4, issues4 = expected_claims(dict(obs, exit_code=obs['exit_code'] + 6))
            assert steps4 == steps and issues4 == issues, labels
            assert {k: v for k, v in claims4.items() if k != 'final_status'} == \
                {k: v for k, v in claims.items() if k != 'final_status'}, labels
        checked += 1
    return checked


def self_check():
    C.self_check()
    properties = _property_checks()
    for example in C.EXAMPLES:
        claims, steps, issues = expected_claims(example.observations)
        assert claims == example.claims, (example.name, claims, example.claims)
        assert steps == example.steps, (example.name, steps, example.steps)
        assert issues == example.issues, (example.name, issues, example.issues)
        assert expected_projections(claims, steps, example.observations) == example.projections, \
            (example.name, expected_projections(claims, steps, example.observations))
        envelope = build_envelope(example.observations)
        accepted = check_record(envelope)
        assert not accepted, (example.name, accepted)
        degraded = deepcopy(envelope)
        runner = degraded['data']['runner_result']
        runner['reporting_failure'] = {'origin': 'runner_host', 'evidence_retained': True,
                                       'original_error': runner['error'],
                                       'original_normalized_outcome': runner['normalized_outcome']}
        runner['normalized_outcome'] = 'runner_reporting_failed'
        runner['error'] = 'runner host could not encode its result: constructed control'
        for step in runner['steps']:
            step['comparison'] = None
        assert not check_record(degraded), (example.name, check_record(degraded))
        # Another response version is refused before any claim is read, even
        # when its record would be accepted under the current version.
        other = build_envelope(example.observations, schema_version=contract.RESPONSE_SCHEMA - 1)
        refused = check_record(other)
        assert refused and refused[0]['kind'] == 'unsupported_version', (example.name, refused)
        without = build_envelope(example.observations)
        del without['data']['runner_result']['runner_subprocess'][C.RECORD_KEY]
        without['data']['runner_sandbox_diagnostics'].update(process_disposition='withheld', termination_cause=C.CAUSE_UNKNOWN,
                                                             stop_reason=None, disposition_integrity='invalid')
        missing = check_record(without)
        assert any(f['kind'] == 'missing_record' for f in missing), (example.name, missing)
        for name, rule, mutated in _mutations(example):
            findings = check_record(mutated)
            assert findings, (example.name, name, 'accepted')
            assert any(f['rule'] == rule for f in findings), (example.name, name, rule, findings)
    total = 0
    for labels, obs in enumerate_model():
        claims, steps, issues = expected_claims(obs)
        for claim in list(claims.values()) + [c for st in steps for c in st.values()]:
            assert claim['state'] in C.CLAIM_STATES, (labels, claim)
        expected_projections(claims, steps, obs)
        findings = check_record(build_envelope(obs))
        invalid_basis = obs['collection_basis'] == 'after_confirmed_reap' and obs['reaped'] is not True
        if invalid_basis:
            assert any(f['kind'] == 'invalid_collection_basis' for f in findings), (labels, findings)
        else:
            assert not findings, (labels, findings)
        total += 1
    assert total == 5 * 6 * 8 * 4 * 3 == properties, (total, properties)
    return {'examples': len(C.EXAMPLES), 'model_rows': total, 'property_rows': properties}


if __name__ == '__main__':
    import json
    import sys
    if '--model-json' in sys.argv:
        # Inputs plus independently expected claims; the Swift test invokes the
        # actual resolver on every row rather than testing this oracle against itself.
        rows = []
        for labels, obs in enumerate_model():
            claims, steps, issues = expected_claims(obs)
            rows.append({'name': '/'.join(labels), 'observations': obs, 'claims': claims, 'steps': steps,
                         'issues': issues, 'projections': expected_projections(claims, steps, obs),
                         'invalid_basis': obs['collection_basis'] == 'after_confirmed_reap' and obs['reaped'] is not True})
        print(json.dumps({'examples': rows}))
    else:
        print(self_check())

"""Lifecycle claim contract for the worker disposition record (test side).

This module is the test-side copy of the contract in
tests/FAILURE-PROPAGATION-CONTRACT.md, section "Worker disposition record".
Tests import every lifecycle spelling from here so that a rename touches one
place. The two copies must agree; `self_check()` is structural, and the
independent checker in tests/lib/lifecycle_oracle.py evaluates the claim tables.

It fixes:

- Wire spellings: question names, claim states, answer values, unresolved and
  inapplicable reason codes, issue kinds, evidence reference tokens, the
  termination-cause labels, the per-step lifecycle summary values and the
  comparison limitations that project it.
- QUESTIONS: for each question, the alternative sufficient witness sets per
  supported answer with the collection scope each needs, the conflict listed
  apart from the answers it disqualifies, the unresolved conditions with their
  reason codes, the forbidden shortcuts, the applicability and its
  inapplicable reason, and the consumers.
- PROJECTIONS: the registered lifecycle projections with their source
  questions, dependencies, absence semantics and named controls.
- EXAMPLES: hand-reviewed observation rows with their expected claims and
  projections. They anchor the independent oracle; the resolver must reproduce
  them, and the oracle's self-check must accept them and reject their mutations.
- The response version that first carries the record and the envelope version
  that first carries the changed controller semantics. The manifest in
  docs/contract.json moves with the producing change (docs/CONTRACT.md).

Witness alternatives are candidate bases after validity and applicability
checks. An applicable conflict disqualifies a supported answer to that question;
it does not erase independent publications or other questions' supported
answers. Answer values, reason codes and the like are wire spellings; question
names are both wire keys and model identifiers.
"""
from collections import namedtuple

# ---------------------------------------------------------------------------
# Versions. Tests assert these minimums; the manifest moves with the producer.
# ---------------------------------------------------------------------------

RESPONSE_WITH_DISPOSITION = 10      # first response schema whose worker replies carry the record
ENVELOPE_WITH_HOST_CAUSE = 3        # first controller envelope with the projected cause and stop reason

# ---------------------------------------------------------------------------
# Wire locations.
# ---------------------------------------------------------------------------

RECORD_KEY = 'disposition'                       # runner_subprocess.disposition
RAW_FACT_KEYS = ('cleanup_trigger', 'grace_end', 'collection_basis')   # new runner_subprocess host facts
STEP_LIFECYCLE_KEY = 'lifecycle'                 # steps[].attempt.lifecycle
DIAGNOSTICS_KEYS = ('process_disposition', 'termination_cause', 'stop_reason',
                    'disposition_integrity', 'disposition_issues')      # runner_sandbox_diagnostics

# ---------------------------------------------------------------------------
# Claim vocabulary.
# ---------------------------------------------------------------------------

CLAIM_STATES = ('supported', 'unresolved', 'conflicting', 'inapplicable')

# Collection scope a witness needs. 'any': holds under every collection basis.
# 'terminal': all relevant reads followed a confirmed reap, so the worker can
# publish nothing more. Negative answers need 'terminal'.
SCOPES = ('any', 'terminal')

RULES = {
    'D1': 'process status',
    'D2': 'host action',
    'D3': 'started/publication',
    'D4': 'not reached',
    'D5': 'publication conflict',
    'D6': 'preservation',
    'D7': 'projection',
    'D8': 'transport',
}

ISSUE_KINDS = ('conflict',)                     # carried in the record
INTEGRITY_ISSUE_KINDS = ('invalid_claim', 'unresolved_reference', 'unrecognized_value',
                         'missing_record', 'malformed_record')          # raised by consumers

# Evidence reference tokens. Run-scoped tokens resolve under runner_subprocess;
# step-scoped tokens resolve inside the record's own step entry.
RUN_REFERENCES = {
    'reaped': 'runner_subprocess.reaped',
    'exit_code': 'runner_subprocess.exit_code',
    'term_signal': 'runner_subprocess.term_signal',
    'poll_stop_reason': 'runner_subprocess.poll_stop_reason',
    'exit_requested': 'runner_subprocess.exit_requested',
    'termination_request': 'runner_subprocess.termination_request',
    'wait_errors': 'runner_subprocess.wait_errors',
    'cleanup_trigger': 'runner_subprocess.cleanup_trigger',
    'grace_end': 'runner_subprocess.grace_end',
    'collection_basis': 'runner_subprocess.collection_basis',
    'done_observed': 'runner_subprocess.done_observed',
    'progress': 'runner_subprocess.worker_evidence.progress',
    'worker_failure': 'runner_subprocess.worker_evidence.failure',
    'plan': 'the submitted probe plan (step count and order)',
}
STEP_REFERENCES = {
    'slot': 'disposition.steps[i].slot',
    'attempt_support': 'disposition.steps[i].attempt_support',
}
REFERENCES = {**RUN_REFERENCES, **STEP_REFERENCES}

# Raw host fact spellings.
POLL_STOP_REASONS = ('done', 'sentinel_deadline', 'child_reaped', 'wait_error', 'policy_write_error')
CLEANUP_TRIGGERS = ('deadline_expiry', 'completion', 'child_reaped', 'poll_wait_error', 'policy_transfer_error')
GRACE_ENDS = ('not_entered', 'reaped_during_grace', 'exhausted', 'wait_error')
COLLECTION_BASES = ('after_confirmed_reap', 'execution_may_continue', 'unavailable')
SLOT_STATES = ('completed', 'incomplete', 'absent')
ATTEMPT_SUPPORT = ('supported', 'unsupported')

# The stop reason that led to each cleanup trigger (the host records the
# trigger at the exit-request store; this is the expected correspondence).
TRIGGER_FOR_STOP = {'sentinel_deadline': 'deadline_expiry', 'done': 'completion',
                    'child_reaped': 'child_reaped', 'wait_error': 'poll_wait_error',
                    'policy_write_error': 'policy_transfer_error'}

# Worker protocol positions (pw_probe_runner_abi.h). Temporal order is the
# protocol's, not the numeric opcode's: proceed (11) precedes attempts (9).
OPERATIONS = {1: 'header', 2: 'policy_read', 3: 'params_create', 4: 'param_set', 5: 'compile',
              6: 'capture', 7: 'ready', 8: 'apply', 9: 'attempt', 10: 'finished', 11: 'proceed'}
PHASES = {1: 'started', 2: 'returned'}
PROTOCOL_ORDER = (1, 2, 3, 4, 5, 6, 7, 8, 11, 9, 10)
OP_ATTEMPT, OP_FINISHED, OP_PARAM_SET = 9, 10, 4
INDEXED_OPERATIONS = {OP_ATTEMPT: 'step_index', OP_PARAM_SET: 'parameter_index'}

# ---------------------------------------------------------------------------
# Question tables.
# ---------------------------------------------------------------------------

Answer = namedtuple('Answer', ['value', 'witnesses', 'rules', 'scope', 'has_value'])
Conflict = namedtuple('Conflict', ['rule', 'witnesses', 'scope'])
Unresolved = namedtuple('Unresolved', ['reason', 'condition'])
Question = namedtuple('Question', [
    'name',           # wire key and model identifier
    'scope_kind',     # 'run' or 'step'
    'answers',        # supported answers
    'conflict',       # Conflict or None
    'unresolved',     # Unresolved conditions with reason codes
    'forbidden',      # shortcuts the D-rules forbid
    'applicability',  # when the question applies
    'inapplicable',   # reason code when it does not
    'consumers',      # projections (or dependent questions) that consume the answer
])


def _answer(value, *witnesses, rules, scope='any', has_value=False):
    return Answer(value, tuple(witnesses), tuple(rules), scope, has_value)


HOST_OBSERVATION = 'direct host observation'
NOT_RECORDED = 'not_recorded'

QUESTIONS = (
    Question(
        'final_status', 'run',
        (_answer('exit_code',
                 'successful reap with a valid exit-status representation and no signal representation',
                 rules=('D1',), has_value=True),
         _answer('signal',
                 'successful reap with a valid signal representation and no exit-status representation',
                 rules=('D1',), has_value=True)),
        Conflict('D1', ('one successful reap represented as both an exit status and a signal',), 'any'),
        (Unresolved('no_successful_reap', 'no successful reap; a successful kill request is not a reap'),
         Unresolved('status_unusable', 'a successful reap with missing, malformed or unrecognized status representation')),
        ('decoding unconfirmed wait storage', 'requiring a successful kill to retain an independently reaped exit'),
        'whenever a worker was spawned', 'no_worker',
        ('runner_sandbox_diagnostics.process_disposition', 'runner_sandbox_diagnostics.termination_cause')),
    Question(
        'stop_reason', 'run',
        tuple(_answer(reason, "the host's poll-loop observation", rules=('D2',)) for reason in POLL_STOP_REASONS),
        None,
        (Unresolved(NOT_RECORDED, 'the host recorded no poll-loop stop'),),
        (),
        'whenever polling started', 'polling_not_started',
        ('runner_sandbox_diagnostics.stop_reason', 'error lifecycle clause')),
    Question(
        'cleanup_trigger', 'run',
        tuple(_answer(trigger, HOST_OBSERVATION + ' of why exit was requested', rules=('D2',))
              for trigger in CLEANUP_TRIGGERS),
        None,
        (Unresolved(NOT_RECORDED, 'the host recorded no trigger apart from the stop reason'),),
        ('reconstructing the trigger from a final exit code',),
        'whenever exit was requested', 'exit_not_requested',
        ('runner_sandbox_diagnostics.termination_cause', 'error lifecycle clause')),
    Question(
        'grace_end', 'run',
        tuple(_answer(end, HOST_OBSERVATION + ' of how the exit-grace wait ended', rules=('D2',))
              for end in GRACE_ENDS),
        None,
        (Unresolved(NOT_RECORDED, 'the host recorded no grace outcome'),),
        ('inferring exhaustion from done plus a kill; a wait error may have ended grace early',),
        'whenever exit was requested', 'exit_not_requested',
        ('runner_sandbox_diagnostics.termination_cause', 'error lifecycle clause')),
    Question(
        'kill_request_and_result', 'run',
        (_answer('none', HOST_OBSERVATION + ' that no termination request was issued', rules=('D2',)),
         _answer('requested', HOST_OBSERVATION + ' of the request and its return', rules=('D2',),
                 has_value=True)),
        None,
        (Unresolved(NOT_RECORDED, 'the host recorded no request outcome'),),
        ('treating a successful request as a reap', 'treating absent request evidence as an observed non-request'),
        'whenever exit was requested', 'exit_not_requested',
        ('runner_sandbox_diagnostics.termination_cause', 'error lifecycle clause')),
    Question(
        'collection_basis', 'run',
        tuple(_answer(basis, HOST_OBSERVATION + ' at collection time', rules=('D2',))
              for basis in COLLECTION_BASES),
        None,
        (Unresolved(NOT_RECORDED, 'the host recorded no basis'),),
        ('stabilizing earlier reads from a later kill request or reap', 'deriving scope from the status axis'),
        'whenever slots were read', 'slots_not_read',
        ('the scope of every per-step answer',)),
    Question(
        'progress_association', 'run',
        (_answer('step_index', 'an attempt-operation word whose item index names a submitted step',
                 rules=('D3',), has_value=True),
         _answer('parameter_index', 'a parameter-indexed operation word', rules=('D3',), has_value=True),
         _answer('none', 'an operation word without an item index', rules=('D3',)),
         _answer('invalid', 'an attempt-operation word whose item index names no submitted step, '
                            'including any attempt index for an empty plan', rules=('D3',))),
        None,
        (Unresolved('no_progress_published', 'no progress word published (raw zero)'),
         Unresolved('progress_unrecognized', 'unrecognized operation or phase code; the raw word is retained')),
        ('reading a parameter index as a step index', 'ordering by numeric opcode instead of the worker protocol'),
        'whenever a progress word was published', 'no_progress_word',
        ('step_boundary_reached', 'step_result_published')),
    Question(
        'step_boundary_reached', 'step',
        (_answer('reached',
                 'valid started or returned attempt progress associated with this step',
                 'a valid completed slot for this supported step, including with absent or unusable progress',
                 'valid attempt progress associated with a later step under the serial attempt order',
                 rules=('D3',)),
         _answer('not_reached',
                 'a valid known protocol position before this step and no completed slot for this step',
                 rules=('D4',), scope='terminal')),
        Conflict('D5', ('a completed slot for this step beside valid terminal progress that never reached it',),
                 'terminal'),
        (Unresolved('no_usable_progress', 'no usable progress and no completed slot'),
         Unresolved('basis_not_terminal', 'a live or unavailable collection basis for not_reached')),
        ('not_reached from missing progress, an unfamiliar opcode, an absent slot or a live snapshot',
         'treating association alone as evidence of execution',
         'treating a started boundary as a native result or as a syscall executing at termination'),
        'every submitted step', 'no_step',
        ('attempt.lifecycle', 'comparison.limitations')),
    Question(
        'step_result_published', 'step',
        (_answer('published', 'a completed slot for this supported step', rules=('D3',)),
         _answer('unpublished', 'a valid incomplete slot for this step with no applicable publication conflict',
                 rules=('D3',), scope='terminal')),
        Conflict('D5', ('valid association, an incomplete slot and valid returned progress for this step '
                        'or a later known protocol position: the completion-before-return rule is violated',),
                 'terminal'),
        (Unresolved('slot_unavailable', 'an absent or unusable slot'),
         Unresolved('basis_not_terminal',
                    'an incomplete slot under a live or unavailable basis, with or without progress beyond it')),
        ('treating a completed slot as proof of successful effect',
         'declaring a protocol violation from reads that can describe different moments',
         'inventing a result for an incomplete slot'),
        'every supported step', 'unsupported_attempt',
        ('attempt.lifecycle', 'runner_subprocess.partial_steps', 'comparison.limitations')),
    Question(
        'step_requested_operation_applicability', 'step',
        (_answer('supported', "the host's attempt mapping resolves the submitted kind and action to a worker "
                              'attempt kind', rules=('D3',)),
         _answer('unsupported', "the host's attempt mapping yields PW_ATTEMPT_NONE", rules=('D3',))),
        None,
        (Unresolved(NOT_RECORDED, 'the host recorded no mapping'),),
        ('treating a completed no-op slot as a completed requested operation',),
        'every submitted step', 'no_step',
        ('attempt.lifecycle', 'attempt.missing_reason')),
)

RUN_QUESTIONS = tuple(q.name for q in QUESTIONS if q.scope_kind == 'run')
STEP_QUESTIONS = tuple(q.name for q in QUESTIONS if q.scope_kind == 'step')
NEGATIVE_ANSWERS = {'step_boundary_reached': 'not_reached', 'step_result_published': 'unpublished'}

# ---------------------------------------------------------------------------
# Projections.
# ---------------------------------------------------------------------------

# runner_sandbox_diagnostics.process_disposition
PROCESS_DISPOSITIONS = ('no_worker', 'unconfirmed', 'clean_exit', 'nonzero_exit', 'signaled',
                        'conflicting', 'withheld', 'unrecognized')
# runner_sandbox_diagnostics.termination_cause. Only the first label is fixed
# for a live witness today (A1); the others follow the same trigger rule.
HOST_SENTINEL_DEADLINE = 'host_sentinel_deadline'
CAUSE_UNKNOWN = 'unknown'
CAUSE_FOR_TRIGGER = {'deadline_expiry': HOST_SENTINEL_DEADLINE,
                     'completion': 'host_exit_grace_exhausted',
                     'poll_wait_error': 'host_cleanup_after_wait_error',
                     'policy_transfer_error': 'host_cleanup_after_transfer_error'}
CAUSE_LABELS = tuple(CAUSE_FOR_TRIGGER.values())
# runner_sandbox_diagnostics.disposition_integrity
INTEGRITY_STATES = ('valid', 'invalid', 'not_reported')
# steps[].attempt.lifecycle.summary
LIFECYCLE_SUMMARIES = ('completed', 'started_without_result', 'not_reached', 'unsupported',
                       'unresolved', 'conflicting')
# comparison.limitations entries projected from the summary (completed adds none)
LIMITATION_FOR_SUMMARY = {'started_without_result': 'attempt:started_without_result',
                          'not_reached': 'attempt:not_reached',
                          'unsupported': 'attempt:unsupported',
                          'unresolved': 'attempt:lifecycle_unresolved',
                          'conflicting': 'attempt:lifecycle_conflicting'}
# Compatibility spellings that stay as they are.
COMPAT_MISSING_OUTCOME = 'not_run_worker_died'
COMPAT_MISSING_REASONS = ('slot_incomplete', 'slot_absent', 'attempt_not_supported')

Projection = namedtuple('Projection', ['name', 'owner', 'source_questions', 'dependencies',
                                       'absence', 'controls'])

PROJECTIONS = (
    Projection('runner_sandbox_diagnostics.process_disposition', 'controller',
               ('final_status',), ('reaped', 'exit_code', 'term_signal'),
               'legacy reply without the record: raw-status compatibility projection; no worker: no_worker',
               {'positive': 'A1 (signaled), A4 (clean_exit), E1', 'negative': 'B1 (conflicting), B4 (unconfirmed)',
                'transport': 'F3 legacy raw projection, E1 invalid record withheld'}),
    Projection('runner_sandbox_diagnostics.termination_cause', 'controller',
               ('final_status', 'cleanup_trigger', 'grace_end', 'kill_request_and_result'),
               ('reaped', 'term_signal', 'exit_code', 'cleanup_trigger', 'grace_end', 'termination_request'),
               'null for a confirmed clean exit; unknown when the record is absent, unresolved, conflicting or unrecognized',
               {'positive': 'A1 (host_sentinel_deadline), A4 (null)', 'negative': 'self-signal stays unknown, B1 unknown',
                'transport': 'E1 unrecognized future label projects to unknown; F3 legacy unknown'}),
    Projection('runner_sandbox_diagnostics.stop_reason', 'controller',
               ('stop_reason',), ('poll_stop_reason',),
               'null when the record is absent or the question is unresolved or inapplicable',
               {'positive': 'A4 (sentinel_deadline beside clean_exit), link 1 (done)', 'negative': 'E2 swapped stop reason',
                'transport': 'F3 legacy null'}),
    Projection('runner_sandbox_diagnostics.disposition_integrity', 'controller',
               ('final_status',) + STEP_QUESTIONS, ('disposition', 'runner_subprocess'),
               'not_reported for a legacy reply; invalid when the record fails validation, with disposition_issues',
               {'positive': 'E1 valid record', 'negative': 'E1 contradicting basis, B1', 'transport': 'F3'}),
    Projection('runner_subprocess.partial_steps', 'runner',
               ('step_result_published',), ('slot', 'attempt_support'),
               'legacy meaning retained: any supported slot not completed',
               {'positive': 'A3 (true), A4 (false)', 'negative': 'D-props adding a completed slot flips it',
                'transport': 'F1 round trip'}),
    Projection('steps[].attempt.lifecycle', 'runner',
               STEP_QUESTIONS, ('progress', 'collection_basis', 'slot', 'attempt_support', 'plan'),
               'absent in legacy replies; required on every step from the record version',
               {'positive': 'A2 started_without_result and not_reached, A3 completed prefix', 'negative': 'E2 swapped answers, B2 unresolved',
                'transport': 'F1 unfamiliar summary value transported'}),
    Projection('steps[].comparison.limitations (attempt:* lifecycle entries)', 'runner',
               STEP_QUESTIONS, ('attempt.lifecycle',),
               'legacy: attempt:slot_incomplete only',
               {'positive': 'A2 limitations agree with lifecycle', 'negative': 'E2 limitation missing',
                'transport': 'F1'}),
    Projection('steps[].attempt.outcome, missing_reason, result_source (compatibility)', 'runner',
               ('step_result_published', 'step_requested_operation_applicability'), ('slot', 'attempt_support'),
               'unchanged spellings; not_run_worker_died means no completed supported result',
               {'positive': 'A2 both steps keep the triple', 'negative': 'worker_sparse_failure pins slot_incomplete',
                'transport': 'F3'}),
    Projection('error (lifecycle clauses)', 'runner',
               ('stop_reason', 'kill_request_and_result', 'final_status'),
               ('poll_stop_reason', 'termination_request', 'reaped', 'exit_code', 'term_signal'),
               'unchanged text; rendered from the account',
               {'positive': 'A1 deadline plus SIGKILL clause, A4 no termination requested', 'negative': 'E3 renderer controls',
                'transport': 'E3 composition with worker failure diagnostics'}),
)

# ---------------------------------------------------------------------------
# Error clause renderer (lifecycle clauses only; text unchanged from today).
# ---------------------------------------------------------------------------

DEADLINE_CLAUSE = 'pw-probe-runner sentinel deadline expired'
KILL_CLAUSE = 'host requested SIGKILL during cleanup'
NO_KILL_CLAUSE = 'no termination requested'
PROBLEM_PREFIX = 'pw-probe-runner: '
PROBLEM_CLAUSES = {
    'unconfirmed': 'process disposition unconfirmed',
    'signal': 'reaped with signal {value}',
    'nonzero_exit': 'reaped with exit code {value}',
    'status_unusable': 'reaped without usable exit status',
    'requested': 'host requested termination during cleanup',
}

# ---------------------------------------------------------------------------
# Hand-reviewed examples: observations -> expected claims and projections.
# ---------------------------------------------------------------------------

MISSING = '<missing>'   # a raw field the reply does not carry (legacy absence)


def observations(**kw):
    """Normalized raw observations. `termination_request` None means observed none."""
    base = {'reaped': None, 'exit_code': None, 'term_signal': None, 'poll_stop_reason': MISSING,
            'exit_requested': None, 'termination_request': MISSING, 'cleanup_trigger': MISSING,
            'grace_end': MISSING, 'collection_basis': MISSING, 'progress': None, 'steps': ()}
    unknown = set(kw) - set(base)
    assert not unknown, unknown
    base.update(kw)
    return base


def step(slot, supported=True):
    return {'slot': slot, 'supported': supported}


def progress(operation, phase, index=None):
    word = {'operation': operation, 'phase': phase,
            'raw': (operation << 24) | (phase << 20) | (0 if index is None else index + 1)}
    if index is not None:
        word['index'] = index
    return word


KILLED_9 = {'signal': 9, 'rc': 0}

Example = namedtuple('Example', ['name', 'observations', 'claims', 'steps', 'issues', 'projections'])


def _supported(answer, value=None):
    claim = {'state': 'supported', 'answer': answer}
    if value is not None:
        claim['value'] = value
    return claim


def _unresolved(reason):
    return {'state': 'unresolved', 'reason': reason}


def _inapplicable(reason):
    return {'state': 'inapplicable', 'reason': reason}


CONFLICTING = {'state': 'conflicting'}

TERMINAL_KILL = dict(reaped=True, term_signal=9, poll_stop_reason='sentinel_deadline', exit_requested=True,
                     termination_request=KILLED_9, cleanup_trigger='deadline_expiry', grace_end='exhausted',
                     collection_basis='after_confirmed_reap')
CLEAN_DONE = dict(reaped=True, exit_code=0, poll_stop_reason='done', exit_requested=True, termination_request=None,
                  cleanup_trigger='completion', grace_end='reaped_during_grace', collection_basis='after_confirmed_reap')
SELF_SIGNAL = dict(reaped=True, term_signal=9, poll_stop_reason='child_reaped', exit_requested=True,
                   termination_request=None, cleanup_trigger='child_reaped', grace_end='not_entered',
                   collection_basis='after_confirmed_reap')

SUPPORTED_STEP = {'step_requested_operation_applicability': _supported('supported')}


def _step(boundary, result):
    return dict(SUPPORTED_STEP, step_boundary_reached=boundary, step_result_published=result)


KILL_CLAIMS = {'final_status': _supported('signal', 9), 'stop_reason': _supported('sentinel_deadline'),
               'cleanup_trigger': _supported('deadline_expiry'), 'grace_end': _supported('exhausted'),
               'kill_request_and_result': _supported('requested', KILLED_9),
               'collection_basis': _supported('after_confirmed_reap')}
DONE_CLAIMS = {'final_status': _supported('exit_code', 0), 'stop_reason': _supported('done'),
               'cleanup_trigger': _supported('completion'), 'grace_end': _supported('reaped_during_grace'),
               'kill_request_and_result': _supported('none'), 'collection_basis': _supported('after_confirmed_reap')}
SELF_SIGNAL_CLAIMS = {'final_status': _supported('signal', 9), 'stop_reason': _supported('child_reaped'),
                      'cleanup_trigger': _supported('child_reaped'), 'grace_end': _supported('not_entered'),
                      'kill_request_and_result': _supported('none'),
                      'collection_basis': _supported('after_confirmed_reap')}

REACHED, NOT_REACHED = _supported('reached'), _supported('not_reached')
PUBLISHED, UNPUBLISHED = _supported('published'), _supported('unpublished')

EXAMPLES = (
    Example('link1_control',
            observations(progress=progress(10, 2), steps=(step('completed'),), **CLEAN_DONE),
            dict(DONE_CLAIMS, progress_association=_supported('none')),
            [_step(REACHED, PUBLISHED)], [],
            {'process_disposition': 'clean_exit', 'termination_cause': None, 'stop_reason': 'done',
             'partial_steps': False, 'summaries': ['completed']}),
    Example('a1_fifo_in_flight',
            observations(progress=progress(9, 1, 0), steps=(step('incomplete'), step('incomplete')), **TERMINAL_KILL),
            dict(KILL_CLAIMS, progress_association=_supported('step_index', 0)),
            [_step(REACHED, UNPUBLISHED), _step(NOT_REACHED, UNPUBLISHED)], [],
            {'process_disposition': 'signaled', 'termination_cause': HOST_SENTINEL_DEADLINE,
             'stop_reason': 'sentinel_deadline', 'partial_steps': True,
             'summaries': ['started_without_result', 'not_reached']}),
    Example('a3_completed_prefix',
            observations(progress=progress(9, 1, 1), steps=(step('completed'), step('incomplete'), step('incomplete')),
                         **TERMINAL_KILL),
            dict(KILL_CLAIMS, progress_association=_supported('step_index', 1)),
            [_step(REACHED, PUBLISHED), _step(REACHED, UNPUBLISHED), _step(NOT_REACHED, UNPUBLISHED)], [],
            {'process_disposition': 'signaled', 'termination_cause': HOST_SENTINEL_DEADLINE,
             'stop_reason': 'sentinel_deadline', 'partial_steps': True,
             'summaries': ['completed', 'started_without_result', 'not_reached']}),
    Example('a4_deadline_then_voluntary_exit',
            observations(reaped=True, exit_code=0, poll_stop_reason='sentinel_deadline', exit_requested=True,
                         termination_request=None, cleanup_trigger='deadline_expiry', grace_end='reaped_during_grace',
                         collection_basis='after_confirmed_reap', progress=progress(10, 2), steps=(step('completed'),)),
            {'final_status': _supported('exit_code', 0), 'stop_reason': _supported('sentinel_deadline'),
             'cleanup_trigger': _supported('deadline_expiry'), 'grace_end': _supported('reaped_during_grace'),
             'kill_request_and_result': _supported('none'), 'collection_basis': _supported('after_confirmed_reap'),
             'progress_association': _supported('none')},
            [_step(REACHED, PUBLISHED)], [],
            {'process_disposition': 'clean_exit', 'termination_cause': None, 'stop_reason': 'sentinel_deadline',
             'partial_steps': False, 'summaries': ['completed']}),
    Example('post_apply_self_signal',
            observations(progress=progress(9, 2, 1), steps=(step('completed'), step('completed')), **SELF_SIGNAL),
            dict(SELF_SIGNAL_CLAIMS, progress_association=_supported('step_index', 1)),
            [_step(REACHED, PUBLISHED), _step(REACHED, PUBLISHED)], [],
            {'process_disposition': 'signaled', 'termination_cause': CAUSE_UNKNOWN, 'stop_reason': 'child_reaped',
             'partial_steps': False, 'summaries': ['completed', 'completed']}),
    Example('b1_conflicting_status',
            observations(progress=progress(10, 2), steps=(step('completed'),), **dict(SELF_SIGNAL, exit_code=0)),
            dict(SELF_SIGNAL_CLAIMS, final_status=CONFLICTING, progress_association=_supported('none')),
            [_step(REACHED, PUBLISHED)],
            [{'kind': 'conflict', 'rule': 'D1', 'question': 'final_status', 'observations': ['exit_code', 'term_signal']}],
            {'process_disposition': 'conflicting', 'termination_cause': CAUSE_UNKNOWN, 'stop_reason': 'child_reaped',
             'partial_steps': False, 'summaries': ['completed']}),
    Example('b4_kill_without_reap',
            observations(reaped=False, poll_stop_reason='sentinel_deadline', exit_requested=True,
                         termination_request=KILLED_9, cleanup_trigger='deadline_expiry', grace_end='exhausted',
                         collection_basis='execution_may_continue', progress=progress(9, 1, 0),
                         steps=(step('incomplete'),)),
            dict(KILL_CLAIMS, final_status=_unresolved('no_successful_reap'),
                 collection_basis=_supported('execution_may_continue'),
                 progress_association=_supported('step_index', 0)),
            [_step(REACHED, _unresolved('basis_not_terminal'))], [],
            {'process_disposition': 'unconfirmed', 'termination_cause': CAUSE_UNKNOWN, 'stop_reason': 'sentinel_deadline',
             'partial_steps': True, 'summaries': ['unresolved']}),
    Example('c3_live_reads_no_conflict',
            observations(reaped=False, poll_stop_reason='sentinel_deadline', exit_requested=True,
                         termination_request={'signal': 9, 'rc': -1, 'errno': 1}, cleanup_trigger='deadline_expiry',
                         grace_end='exhausted', collection_basis='execution_may_continue', progress=progress(9, 2, 0),
                         steps=(step('incomplete'),)),
            dict(KILL_CLAIMS, final_status=_unresolved('no_successful_reap'),
                 kill_request_and_result=_supported('requested', {'signal': 9, 'rc': -1, 'errno': 1}),
                 collection_basis=_supported('execution_may_continue'),
                 progress_association=_supported('step_index', 0)),
            [_step(REACHED, _unresolved('basis_not_terminal'))], [],
            {'process_disposition': 'unconfirmed', 'termination_cause': CAUSE_UNKNOWN, 'stop_reason': 'sentinel_deadline',
             'partial_steps': True, 'summaries': ['unresolved']}),
    Example('c4_terminal_publication_conflict',
            observations(progress=progress(9, 2, 1), steps=(step('completed'), step('incomplete')), **CLEAN_DONE),
            dict(DONE_CLAIMS, progress_association=_supported('step_index', 1)),
            [_step(REACHED, PUBLISHED), _step(REACHED, CONFLICTING)],
            [{'kind': 'conflict', 'rule': 'D5', 'question': 'step_result_published', 'step_index': 1,
              'observations': ['progress', 'slot', 'collection_basis']}],
            {'process_disposition': 'clean_exit', 'termination_cause': None, 'stop_reason': 'done',
             'partial_steps': True, 'summaries': ['completed', 'conflicting']}),
    Example('b3_unrecognized_opcode_keeps_results',
            observations(progress=progress(200, 1, 0), steps=(step('completed'), step('completed')), **CLEAN_DONE),
            dict(DONE_CLAIMS, progress_association=_unresolved('progress_unrecognized')),
            [_step(REACHED, PUBLISHED), _step(REACHED, PUBLISHED)], [],
            {'process_disposition': 'clean_exit', 'termination_cause': None, 'stop_reason': 'done',
             'partial_steps': False, 'summaries': ['completed', 'completed']}),
    Example('b5_out_of_range_index',
            observations(progress=progress(9, 1, 2), steps=(step('incomplete'), step('incomplete')), **TERMINAL_KILL),
            dict(KILL_CLAIMS, progress_association=_supported('invalid')),
            [_step(_unresolved('no_usable_progress'), UNPUBLISHED), _step(_unresolved('no_usable_progress'), UNPUBLISHED)],
            [],
            {'process_disposition': 'signaled', 'termination_cause': HOST_SENTINEL_DEADLINE,
             'stop_reason': 'sentinel_deadline', 'partial_steps': True, 'summaries': ['unresolved', 'unresolved']}),
    Example('b6_unsupported_completed_noop',
            observations(progress=progress(10, 2), steps=(step('completed', supported=False),), **CLEAN_DONE),
            dict(DONE_CLAIMS, progress_association=_supported('none')),
            [{'step_requested_operation_applicability': _supported('unsupported'),
              'step_boundary_reached': REACHED, 'step_result_published': _inapplicable('unsupported_attempt')}],
            [],
            {'process_disposition': 'clean_exit', 'termination_cause': None, 'stop_reason': 'done',
             'partial_steps': False, 'summaries': ['unsupported']}),
    Example('b2_missing_progress_incomplete_slot',
            observations(progress=None, steps=(step('incomplete'),), **TERMINAL_KILL),
            dict(KILL_CLAIMS, progress_association=_inapplicable('no_progress_word')),
            [_step(_unresolved('no_usable_progress'), UNPUBLISHED)], [],
            {'process_disposition': 'signaled', 'termination_cause': HOST_SENTINEL_DEADLINE,
             'stop_reason': 'sentinel_deadline', 'partial_steps': True, 'summaries': ['unresolved']}),
    Example('pre_apply_deadline_compile_started',
            observations(progress=progress(5, 1), steps=(step('incomplete'), step('incomplete')), **TERMINAL_KILL),
            dict(KILL_CLAIMS, progress_association=_supported('none')),
            [_step(NOT_REACHED, UNPUBLISHED), _step(NOT_REACHED, UNPUBLISHED)], [],
            {'process_disposition': 'signaled', 'termination_cause': HOST_SENTINEL_DEADLINE,
             'stop_reason': 'sentinel_deadline', 'partial_steps': True, 'summaries': ['not_reached', 'not_reached']}),
    Example('nonzero_exit_before_apply',
            observations(progress=progress(5, 2), steps=(step('incomplete'),),
                         **dict(SELF_SIGNAL, term_signal=None, exit_code=17)),
            dict(SELF_SIGNAL_CLAIMS, final_status=_supported('exit_code', 17), progress_association=_supported('none')),
            [_step(NOT_REACHED, UNPUBLISHED)], [],
            {'process_disposition': 'nonzero_exit', 'termination_cause': CAUSE_UNKNOWN, 'stop_reason': 'child_reaped',
             'partial_steps': True, 'summaries': ['not_reached']}),
    Example('completed_then_grace_exhausted_kill',
            observations(reaped=True, term_signal=9, poll_stop_reason='done', exit_requested=True,
                         termination_request=KILLED_9, cleanup_trigger='completion', grace_end='exhausted',
                         collection_basis='after_confirmed_reap', progress=progress(10, 2), steps=(step('completed'),)),
            {'final_status': _supported('signal', 9), 'stop_reason': _supported('done'),
             'cleanup_trigger': _supported('completion'), 'grace_end': _supported('exhausted'),
             'kill_request_and_result': _supported('requested', KILLED_9),
             'collection_basis': _supported('after_confirmed_reap'), 'progress_association': _supported('none')},
            [_step(REACHED, PUBLISHED)], [],
            {'process_disposition': 'signaled', 'termination_cause': 'host_exit_grace_exhausted', 'stop_reason': 'done',
             'partial_steps': False, 'summaries': ['completed']}),
    Example('legacy_host_facts_missing',
            observations(reaped=True, term_signal=9, progress=None, steps=(step('incomplete'),)),
            {'final_status': _supported('signal', 9), 'stop_reason': _unresolved(NOT_RECORDED),
             'cleanup_trigger': _unresolved(NOT_RECORDED), 'grace_end': _unresolved(NOT_RECORDED),
             'kill_request_and_result': _unresolved(NOT_RECORDED), 'collection_basis': _unresolved(NOT_RECORDED),
             'progress_association': _inapplicable('no_progress_word')},
            [_step(_unresolved('no_usable_progress'), _unresolved('basis_not_terminal'))], [],
            {'process_disposition': 'signaled', 'termination_cause': CAUSE_UNKNOWN, 'stop_reason': None,
             'partial_steps': True, 'summaries': ['unresolved']}),
    Example('empty_plan_attempt_word',
            observations(progress=progress(9, 1, 0), steps=(), **TERMINAL_KILL),
            dict(KILL_CLAIMS, progress_association=_supported('invalid')),
            [], [],
            {'process_disposition': 'signaled', 'termination_cause': HOST_SENTINEL_DEADLINE,
             'stop_reason': 'sentinel_deadline', 'partial_steps': False, 'summaries': []}),
)


# ---------------------------------------------------------------------------
# Lookups and structural self-check.
# ---------------------------------------------------------------------------

def question(name):
    for entry in QUESTIONS:
        if entry.name == name:
            return entry
    raise KeyError(name)


def answer(name, value):
    for entry in question(name).answers:
        if entry.value == value:
            return entry
    raise KeyError((name, value))


def reasons(name):
    return tuple(u.reason for u in question(name).unresolved)


def self_check():
    """Structural checks; the independent oracle evaluates the claim tables."""
    names = [entry.name for entry in QUESTIONS]
    assert len(names) == len(set(names)), names
    for entry in QUESTIONS:
        assert entry.name.isidentifier() and entry.name == entry.name.lower(), entry.name
        assert entry.scope_kind in ('run', 'step'), entry.name
        assert entry.answers, entry.name
        values = [a.value for a in entry.answers]
        assert len(values) == len(set(values)), entry.name
        supporting = set()
        for a in entry.answers:
            assert a.value and a.value.isidentifier(), (entry.name, a.value)
            assert a.witnesses and all(isinstance(w, str) and w for w in a.witnesses), (entry.name, a)
            assert a.rules and set(a.rules) <= set(RULES), (entry.name, a)
            assert a.scope in SCOPES, (entry.name, a)
            supporting.update(a.witnesses)
        if entry.conflict is not None:
            assert entry.conflict.rule in RULES and entry.conflict.scope in SCOPES, entry.name
            assert entry.conflict.witnesses, entry.name
            # Catch identical table entries in both roles. Semantic overlap of a
            # supporting basis with a larger conflict witness needs the D-model.
            assert not supporting & set(entry.conflict.witnesses), entry.name
        codes = [u.reason for u in entry.unresolved]
        assert codes and len(codes) == len(set(codes)) and all(c.isidentifier() for c in codes), entry.name
        assert all(u.condition for u in entry.unresolved), entry.name
        assert all(isinstance(f, str) and f for f in entry.forbidden), entry.name
        assert entry.applicability and entry.inapplicable.isidentifier(), entry.name
        assert entry.consumers and all(isinstance(c, str) and c for c in entry.consumers), entry.name
    for name, value in NEGATIVE_ANSWERS.items():
        assert answer(name, value).scope == 'terminal', (name, value)
    assert tuple(a.value for a in question('stop_reason').answers) == POLL_STOP_REASONS
    assert tuple(a.value for a in question('cleanup_trigger').answers) == CLEANUP_TRIGGERS
    assert tuple(a.value for a in question('grace_end').answers) == GRACE_ENDS
    assert tuple(a.value for a in question('collection_basis').answers) == COLLECTION_BASES
    assert set(TRIGGER_FOR_STOP) == set(POLL_STOP_REASONS) and set(TRIGGER_FOR_STOP.values()) == set(CLEANUP_TRIGGERS)
    assert set(CAUSE_FOR_TRIGGER) == set(CLEANUP_TRIGGERS) - {'child_reaped'}
    assert HOST_SENTINEL_DEADLINE in CAUSE_LABELS and CAUSE_UNKNOWN not in CAUSE_LABELS
    assert set(PROTOCOL_ORDER) == set(OPERATIONS)
    assert set(LIMITATION_FOR_SUMMARY) == set(LIFECYCLE_SUMMARIES) - {'completed'}
    for projection in PROJECTIONS:
        assert projection.name and projection.owner in ('runner', 'controller'), projection
        assert projection.source_questions and set(projection.source_questions) <= set(names), projection.name
        assert projection.dependencies and projection.absence, projection.name
        assert set(projection.controls) == {'positive', 'negative', 'transport'}, projection.name
        assert all(projection.controls.values()), projection.name
    seen = set()
    for example in EXAMPLES:
        assert example.name not in seen, example.name
        seen.add(example.name)
        assert set(example.claims) == set(RUN_QUESTIONS), example.name
        assert len(example.steps) == len(example.observations['steps']), example.name
        for claims in example.steps:
            assert set(claims) == set(STEP_QUESTIONS), example.name
        for claims in (example.claims, *example.steps):
            for name, claim in claims.items():
                assert claim['state'] in CLAIM_STATES, (example.name, name)
                if claim['state'] == 'supported':
                    entry = answer(name, claim['answer'])
                    assert ('value' in claim) == entry.has_value, (example.name, name)
                elif claim['state'] == 'unresolved':
                    assert claim['reason'] in reasons(name), (example.name, name, claim)
                elif claim['state'] == 'inapplicable':
                    assert claim['reason'] == question(name).inapplicable, (example.name, name, claim)
        conflicting = [(n, None) for n, c in example.claims.items() if c['state'] == 'conflicting']
        conflicting += [(n, i) for i, claims in enumerate(example.steps) for n, c in claims.items() if c['state'] == 'conflicting']
        assert len(conflicting) == len(example.issues), example.name
        for issue in example.issues:
            assert issue['kind'] in ISSUE_KINDS and issue['rule'] in RULES, (example.name, issue)
            assert (issue['question'], issue.get('step_index')) in conflicting, (example.name, issue)
            assert issue['observations'] and set(issue['observations']) <= set(REFERENCES), (example.name, issue)
        assert example.projections['process_disposition'] in PROCESS_DISPOSITIONS, example.name
        cause = example.projections['termination_cause']
        assert cause is None or cause == CAUSE_UNKNOWN or cause in CAUSE_LABELS, example.name
        assert all(s in LIFECYCLE_SUMMARIES for s in example.projections['summaries']), example.name
        assert len(example.projections['summaries']) == len(example.steps), example.name
    assert RESPONSE_WITH_DISPOSITION > 9 and ENVELOPE_WITH_HOST_CAUSE > 2
    return True


if __name__ == '__main__':
    self_check()
    answers = sum(len(entry.answers) for entry in QUESTIONS)
    conflicts = sum(entry.conflict is not None for entry in QUESTIONS)
    print(f'{len(QUESTIONS)} questions, {answers} answers, {conflicts} conflict rules, {len(PROJECTIONS)} projections, '
          f'{len(EXAMPLES)} examples, {len(CAUSE_LABELS)} cause labels')

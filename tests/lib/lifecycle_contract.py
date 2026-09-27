"""Lifecycle claim contract for the worker disposition record (test side).

Skeleton for controller/DISPOSITION-RECORD-PLAN.md. Tests that name a lifecycle
constant import it from here so that a rename touches one place. This module
fixes two things now:

- HOST_SENTINEL_DEADLINE: the one termination-cause label the plan fixes before
  the contract stage so that red test A1 is runnable. It projects a witnessed
  host cleanup sequence: deadline expiry, a successful host termination request
  and a matching reaped signal. It is not exclusive signal-sender attribution
  and not a sandbox cause.
- QUESTIONS: the fixed list of lifecycle questions the record answers. Each
  supported answer lists its alternative sufficient witness sets, the D-rules
  that govern it and the collection scope it needs. Conflicts are listed apart
  from the answers they disqualify: a conflict witness never supports an answer.
  Unresolved conditions name the missing or unusable witness. The plan's
  "The questions the record answers" tables carry the same content, and the two
  must agree.

Witness alternatives are candidate bases after validity and applicability
checks. An applicable conflict disqualifies a supported answer to that question;
it does not erase independent publications or other questions' supported answers.
The string-level self-check below cannot establish this semantic precedence.

Everything else belongs to the contract stage and is deliberately absent: reason
and issue codes, lifecycle value spellings, the trigger-to-cause table beyond the
one label, the projection inventory's dependency sets and named controls, and
the claim tables the D-model evaluates. Do not add a placeholder spelling here
for an open value.

Question names, answer values, claim states, scopes and rule identifiers are
model vocabulary for tests and the independent oracle, not wire spellings, except
where an answer names an existing envelope spelling. Consumers are the plan's
names for projections (or dependent questions); a projection that does not exist
in the envelope today is provisional until the contract stage fixes it.
"""
from collections import namedtuple

# The one cause label fixed now (plan: "Claim requirements and projection
# inventory"). Value of runner_sandbox_diagnostics.termination_cause when the
# host's deadline fired, its termination request succeeded and the reaped
# signal matches that request.
HOST_SENTINEL_DEADLINE = 'host_sentinel_deadline'

# Every question has exactly one of these states in a resolved record.
CLAIM_STATES = ('supported', 'unresolved', 'conflicting', 'inapplicable')

# Collection scope a witness needs. 'any': holds under every collection basis.
# 'terminal': all relevant reads followed a confirmed reap, so the worker can
# publish nothing more. Negative answers need 'terminal'.
SCOPES = ('any', 'terminal')

# Seed claim rules (plan: "Claim requirements and projection inventory").
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

# Existing raw spellings of runner_subprocess.poll_stop_reason. The stop-reason
# question answers with them; they are not new constants.
POLL_STOP_REASONS = ('done', 'sentinel_deadline', 'child_reaped', 'wait_error', 'policy_write_error')

Answer = namedtuple('Answer', [
    'value',      # the supported answer
    'witnesses',  # alternative sufficient witness sets; any one suffices
    'rules',      # D-rules that govern this answer
    'scope',      # collection scope the witnesses need
])

Conflict = namedtuple('Conflict', [
    'rule',       # the D-rule the observations violate
    'witnesses',  # the incompatible observations, once valid and in scope
    'scope',      # collection scope in which the rule applies
])

Question = namedtuple('Question', [
    'name',           # model identifier
    'answers',        # supported answers
    'conflict',       # Conflict or None
    'unresolved',     # conditions that leave the question unresolved
    'forbidden',      # shortcuts the D-rules forbid
    'applicability',  # when the question applies at all
    'consumers',      # projections (or dependent questions) that consume the answer
])


def _answer(value, *witnesses, rules, scope='any'):
    return Answer(value, tuple(witnesses), tuple(rules), scope)


HOST_OBSERVATION = 'direct host observation'

QUESTIONS = (
    Question(
        'final_status',
        (_answer('exit code',
                 'successful reap with a valid exit-status representation and no signal representation',
                 rules=('D1',)),
         _answer('signal',
                 'successful reap with a valid signal representation and no exit-status representation',
                 rules=('D1',))),
        Conflict('D1', ('one successful reap represented as both an exit status and a signal',), 'any'),
        ('no successful reap; a successful kill request is not a reap',
         'a successful reap with missing, malformed or unrecognized status representation'),
        ('decoding unconfirmed wait storage', 'requiring a successful kill to retain an independently reaped exit'),
        'whenever a worker was spawned',
        ('runner_sandbox_diagnostics.process_disposition', 'runner_sandbox_diagnostics.termination_cause')),
    Question(
        'stop_reason',
        tuple(_answer(reason, "the host's poll-loop observation", rules=('D2',)) for reason in POLL_STOP_REASONS),
        None,
        ('the host recorded no poll-loop stop',),
        (),
        'whenever polling started',
        ('runner_sandbox_diagnostics.stop_reason', 'error lifecycle clause')),
    Question(
        'cleanup_trigger',
        (_answer('deadline expiry', HOST_OBSERVATION + ' of why exit was requested', rules=('D2',)),
         _answer('completion', HOST_OBSERVATION + ' of why exit was requested', rules=('D2',)),
         _answer('child reaped during polling', HOST_OBSERVATION + ' of why exit was requested', rules=('D2',)),
         _answer('poll wait error', HOST_OBSERVATION + ' of why exit was requested', rules=('D2',)),
         _answer('policy transfer error', HOST_OBSERVATION + ' of why exit was requested', rules=('D2',))),
        None,
        ('the host recorded no trigger apart from the stop reason',),
        ('reconstructing the trigger from a final exit code',),
        'whenever exit was requested',
        ('runner_sandbox_diagnostics.termination_cause', 'error lifecycle clause')),
    Question(
        'grace_end',
        (_answer('not entered', HOST_OBSERVATION + ' of how the exit-grace wait ended', rules=('D2',)),
         _answer('reap during grace', HOST_OBSERVATION + ' of how the exit-grace wait ended', rules=('D2',)),
         _answer('exhaustion', HOST_OBSERVATION + ' of how the exit-grace wait ended', rules=('D2',)),
         _answer('wait error', HOST_OBSERVATION + ' of how the exit-grace wait ended', rules=('D2',))),
        None,
        ('the host recorded no grace outcome',),
        ('inferring exhaustion from done plus a kill; a wait error may have ended grace early',),
        'whenever exit was requested',
        ('runner_sandbox_diagnostics.termination_cause', 'error lifecycle clause')),
    Question(
        'kill_request_and_result',
        (_answer('none', HOST_OBSERVATION + ' that no termination request was issued', rules=('D2',)),
         _answer('requested, with rc and errno', HOST_OBSERVATION + ' of the request and its return',
                 rules=('D2',))),
        None,
        ('the host recorded no request outcome',),
        ('treating a successful request as a reap', 'treating absent request evidence as an observed non-request'),
        'whenever cleanup ran',
        ('runner_sandbox_diagnostics.termination_cause', 'error lifecycle clause')),
    Question(
        'collection_basis',
        (_answer('reads after confirmed reap', HOST_OBSERVATION + ' at collection time', rules=('D2',)),
         _answer('reads while execution may continue', HOST_OBSERVATION + ' at collection time', rules=('D2',)),
         _answer('unavailable', HOST_OBSERVATION + ' at collection time', rules=('D2',))),
        None,
        ('the host recorded no basis',),
        ('stabilizing earlier reads from a later kill request or reap', 'deriving scope from the status axis'),
        'whenever slots were read',
        ('the scope of every per-step answer',)),
    Question(
        'progress_association',
        (_answer('valid step index', 'an attempt-operation word whose item index names a submitted step',
                 rules=('D3',)),
         _answer('parameter index', 'a parameter-indexed operation word', rules=('D3',)),
         _answer('none', 'an operation word without an item index', rules=('D3',)),
         _answer('invalid', 'an attempt-operation word whose item index names no submitted step, '
                            'including any attempt index for an empty plan', rules=('D3',))),
        None,
        ('no progress word published', 'unrecognized operation or phase code; the raw word is retained'),
        ('reading a parameter index as a step index', 'ordering by numeric opcode instead of the worker protocol'),
        'whenever a progress word was published',
        ('step_boundary_reached', 'step_result_published')),
    Question(
        'step_boundary_reached',
        (_answer('reached',
                 'valid started or returned attempt progress associated with this step',
                 'a valid completed slot for this supported step, including with absent or unusable progress',
                 'valid attempt progress associated with a later step under the serial attempt order',
                 rules=('D3',)),
         _answer('not reached',
                 'a valid known protocol position before this step and no completed slot for this step',
                 rules=('D4',), scope='terminal')),
        Conflict('D5', ('a completed slot for this step beside valid terminal progress that never reached it',),
                 'terminal'),
        ('no usable progress and no completed slot', 'a live or unavailable collection basis for not reached'),
        ('not reached from missing progress, an unfamiliar opcode, an absent slot or a live snapshot',
         'treating association alone as evidence of execution',
         'treating a started boundary as a native result or as a syscall executing at termination'),
        'every submitted step',
        ('attempt.lifecycle', 'comparison.limitations')),
    Question(
        'step_result_published',
        (_answer('published', 'a completed slot for this supported step', rules=('D3',)),
         _answer('unpublished', 'a valid incomplete slot for this step with no applicable publication conflict',
                 rules=('D3',), scope='terminal')),
        Conflict('D5', ('valid association, an incomplete slot and valid returned progress for this step '
                        'or a later known protocol position: '
                        'the completion-before-return rule is violated',), 'terminal'),
        ('an absent or unusable slot',
         'an incomplete slot under a live or unavailable basis, with or without progress beyond it'),
        ('treating a completed slot as proof of successful effect',
         'declaring a protocol violation from reads that can describe different moments',
         'inventing a result for an incomplete slot'),
        'every supported step',
        ('attempt.lifecycle', 'runner_subprocess.partial_steps', 'comparison.limitations')),
    Question(
        'step_requested_operation_applicability',
        (_answer('supported', "the host's attempt mapping resolves the submitted kind and action to a worker "
                              'attempt kind', rules=('D3',)),
         _answer('unsupported', "the host's attempt mapping yields PW_ATTEMPT_NONE", rules=('D3',))),
        None,
        ('the host recorded no mapping',),
        ('treating a completed no-op slot as a completed requested operation',),
        'every submitted step',
        ('attempt.lifecycle', 'attempt.missing_reason')),
)

# Negative answers can only be supported once the worker can publish no more.
NEGATIVE_ANSWERS = {'step_boundary_reached': 'not reached', 'step_result_published': 'unpublished'}


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


def self_check():
    """Structural checks only; the contract stage adds the semantic ones."""
    names = [entry.name for entry in QUESTIONS]
    assert len(names) == len(set(names)), names
    for entry in QUESTIONS:
        assert entry.name.isidentifier() and entry.name == entry.name.lower(), entry.name
        assert entry.answers, entry.name
        values = [a.value for a in entry.answers]
        assert len(values) == len(set(values)), entry.name
        supporting = set()
        for a in entry.answers:
            assert a.value and a.witnesses and all(isinstance(w, str) and w for w in a.witnesses), (entry.name, a)
            assert a.rules and set(a.rules) <= set(RULES), (entry.name, a)
            assert a.scope in SCOPES, (entry.name, a)
            supporting.update(a.witnesses)
        if entry.conflict is not None:
            assert entry.conflict.rule in RULES and entry.conflict.scope in SCOPES, entry.name
            assert entry.conflict.witnesses, entry.name
            # Catch identical table entries in both roles. Semantic overlap of a
            # supporting basis with a larger conflict witness needs the D-model.
            assert not supporting & set(entry.conflict.witnesses), entry.name
        assert all(isinstance(u, str) and u for u in entry.unresolved), entry.name
        assert all(isinstance(f, str) and f for f in entry.forbidden), entry.name
        assert entry.applicability, entry.name
        assert entry.consumers and all(isinstance(c, str) and c for c in entry.consumers), entry.name
    for name, value in NEGATIVE_ANSWERS.items():
        assert answer(name, value).scope == 'terminal', (name, value)
    assert tuple(a.value for a in question('stop_reason').answers) == POLL_STOP_REASONS
    assert {'cleanup_trigger', 'grace_end'} <= set(names)
    assert HOST_SENTINEL_DEADLINE.isidentifier() and HOST_SENTINEL_DEADLINE == HOST_SENTINEL_DEADLINE.lower()
    assert HOST_SENTINEL_DEADLINE != 'unknown'
    return True


if __name__ == '__main__':
    self_check()
    answers = sum(len(entry.answers) for entry in QUESTIONS)
    conflicts = sum(entry.conflict is not None for entry in QUESTIONS)
    print(f'{len(QUESTIONS)} questions, {answers} answers, {conflicts} conflict rules, {len(RULES)} rules, '
          f'1 fixed cause label ({HOST_SENTINEL_DEADLINE})')

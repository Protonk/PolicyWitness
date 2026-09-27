"""Lifecycle claim contract for the worker disposition record (test side).

Skeleton for controller/DISPOSITION-RECORD-PLAN.md. Tests that name a lifecycle
constant import it from here so that a rename touches one place. This module
fixes two things now:

- HOST_SENTINEL_DEADLINE: the one termination-cause label the plan fixes before
  the contract stage so that red test A1 is runnable. It projects a witnessed
  host cleanup sequence: deadline expiry, a successful host termination request
  and a matching reaped signal. It is not exclusive signal-sender attribution
  and not a sandbox cause.
- QUESTIONS: the fixed list of lifecycle questions the record answers, with the
  answer domain, sufficient witnesses, D-rules, applicability and consumers
  transcribed from the plan's question table.

Everything else belongs to the contract stage and is deliberately absent: reason
and issue codes, lifecycle value spellings, the trigger-to-cause table beyond the
one label, the projection inventory's dependency sets and named controls, and
the claim tables the D-model evaluates. Do not add a placeholder spelling here
for an open value.

Question names, claim states and rule identifiers are model vocabulary for
tests and the independent oracle, not wire spellings. Answer-domain entries are
descriptive except where they name an existing envelope spelling. Consumers are
the plan's names for projections (or dependent questions); a projection that
does not exist in the envelope today is provisional until the contract stage
fixes it.
"""
from collections import namedtuple

# The one cause label fixed now (plan: "Claim requirements and projection
# inventory"). Value of runner_sandbox_diagnostics.termination_cause when the
# host's deadline fired, its termination request succeeded and the reaped
# signal matches that request.
HOST_SENTINEL_DEADLINE = 'host_sentinel_deadline'

# Every question has exactly one of these states in a resolved record.
CLAIM_STATES = ('supported', 'unresolved', 'conflicting', 'inapplicable')

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

Question = namedtuple('Question', [
    'name',                  # model identifier
    'answer_domain',         # descriptive answers, or existing spellings
    'sufficient_witnesses',  # what supports a supported answer
    'rules',                 # D-rules that govern the answer
    'applicability',         # when the question applies at all
    'consumers',             # projections (or dependent questions) that consume the answer
])

QUESTIONS = (
    Question('final_status',
             ('exit code', 'signal'),
             'successful reap plus one valid status representation', ('D1',),
             'whenever a worker was spawned',
             ('runner_sandbox_diagnostics.process_disposition',
              'runner_sandbox_diagnostics.termination_cause')),
    Question('stop_reason',
             POLL_STOP_REASONS,
             "the host's poll-loop observation", ('D2',),
             'whenever polling started',
             ('runner_sandbox_diagnostics.stop_reason', 'error lifecycle clause')),
    Question('cleanup_trigger_and_grace_end',
             ('not entered', 'reap during grace', 'exhaustion', 'wait error'),
             'direct host observation', ('D2',),
             'whenever exit was requested',
             ('runner_sandbox_diagnostics.termination_cause', 'error lifecycle clause')),
    Question('kill_request_and_result',
             ('none', 'requested, with rc and errno'),
             'direct host observation', ('D2',),
             'whenever cleanup ran',
             ('runner_sandbox_diagnostics.termination_cause', 'error lifecycle clause')),
    Question('collection_basis',
             ('reads after confirmed reap', 'reads while execution may continue', 'unavailable'),
             'direct host observation at collection', ('D2',),
             'whenever slots were read',
             ('the scope of every per-step answer',)),
    Question('progress_association',
             ('valid step index', 'parameter index', 'none', 'invalid'),
             'the decoded word validated against the submitted plan', ('D3',),
             'whenever a progress word was published',
             ('step_boundary_reached', 'step_result_published')),
    Question('step_boundary_reached',
             ('reached', 'not reached'),
             'progress at or beyond the step under terminal scope', ('D3', 'D4'),
             'every submitted step',
             ('attempt.lifecycle', 'comparison.limitations')),
    Question('step_result_published',
             ('published', 'unpublished'),
             'a completed slot, or progress beyond an incomplete slot under terminal scope',
             ('D3', 'D5'),
             'every supported step',
             ('attempt.lifecycle', 'runner_subprocess.partial_steps', 'comparison.limitations')),
    Question('step_requested_operation_applicability',
             ('supported', 'unsupported'),
             "the host's attempt mapping", (),
             'every submitted step',
             ('attempt.lifecycle', 'attempt.missing_reason')),
)


def question(name):
    for entry in QUESTIONS:
        if entry.name == name:
            return entry
    raise KeyError(name)


def self_check():
    """Structural checks only; the contract stage adds the semantic ones."""
    names = [entry.name for entry in QUESTIONS]
    assert len(names) == len(set(names)), names
    for entry in QUESTIONS:
        assert entry.name.isidentifier() and entry.name == entry.name.lower(), entry.name
        assert entry.answer_domain and all(isinstance(a, str) and a for a in entry.answer_domain), entry
        assert entry.sufficient_witnesses and entry.applicability, entry
        assert set(entry.rules) <= set(RULES), entry
        assert entry.consumers and all(isinstance(c, str) and c for c in entry.consumers), entry
    assert question('stop_reason').answer_domain == POLL_STOP_REASONS
    assert HOST_SENTINEL_DEADLINE.isidentifier() and HOST_SENTINEL_DEADLINE == HOST_SENTINEL_DEADLINE.lower()
    assert HOST_SENTINEL_DEADLINE != 'unknown'
    return True


if __name__ == '__main__':
    self_check()
    print(f'{len(QUESTIONS)} questions, {len(RULES)} rules, 1 fixed cause label ({HOST_SENTINEL_DEADLINE})')

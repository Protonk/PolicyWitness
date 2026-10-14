"""Death after the native return and before publication withholds the result.

One specimen under (version 1) (allow default) with --no-log-capture:

- prefix: open_read /etc/hosts. Completes and must survive.
- created: create <staging>/created.txt with worker_kill_before_publish_slot: 1.
  The worker's open(O_CREAT) returns and the slot's fields are written; the
  seam then raises SIGKILL before the slot's `completed` flag is stored.
- after: open_read /etc/hosts. Never reached.

The check observes the created file itself before reading any JSON: the native
operation happened. The reply must not know that. It reports the slot as
no_completed_result with started_without_result, withholds rc and errno, keeps
the completed prefix and marks the last step not_reached. The host's own
witnesses (child_reaped, term_signal 9, the started progress word for index 1)
establish the position; the echoed override is setup, not proof the seam fired.

Staging lives under /private/tmp and is removed only when the envelope
witnesses the worker's exit (tests/lib/worker_exit_witness.py).
"""
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import consumer
import lifecycle_oracle
from lifecycle_adapter import read_lifecycle, summaries
from run_capture import RunCapture
from worker_exit_witness import worker_exit_witness

CLI_ARGS = ['--no-log-capture', '--timeout-ms', '20000']
HARNESS_WAIT_SECONDS = 60
# The seam ends the worker within the attempt; the sentinel is a bound, not the trigger.
OVERRIDES = {'worker_kill_before_publish_slot': 1, 'worker_timeout_ms': 5000}
POLICY = {'format': 'sbpl', 'sbpl_source': '(version 1) (allow default)'}
MISSING = 'no_completed_result'
# Words that would turn a missing result into a claim about execution.
FORBIDDEN_ERROR_WORDS = ('not run', 'never ran', 'did not run', 'never started', 'not started', 'did not start')


def progress_word(operation, phase, index=None):
    word = (operation << 24) | (phase << 20) | (0 if index is None else index + 1)
    decoded = {'operation': operation, 'stage': phase, 'raw': word}
    if index is not None:
        decoded['index'] = index
    return decoded


STARTED_ATTEMPT_1 = progress_word(9, 1, 1)  # PW_OP_ATTEMPT, PW_PROGRESS_STARTED, slot 1


def read_step(step_id, target):
    return {'step_id': step_id,
            'sandbox_check': {'operation': 'file-read-data', 'filter': {'kind': 'path', 'value': str(target)}},
            'attempt': {'kind': 'file', 'action': 'open_read', 'target': str(target)}}


def create_step(step_id, target):
    return {'step_id': step_id,
            'sandbox_check': {'operation': 'file-write-create', 'filter': {'kind': 'path', 'value': str(target)}},
            'attempt': {'kind': 'file', 'action': 'create', 'target': str(target)}}


def specimen(target):
    return {'schema_version': 4, 'specimen_id': 'killed_before_publication', 'policy': dict(POLICY),
            'probe_plan': [read_step('prefix', '/etc/hosts'), create_step('created', target),
                           read_step('after', '/etc/hosts')],
            '_test_overrides': dict(OVERRIDES)}


def witnesses(envelope):
    runner = envelope['data']['runner_result']
    sub = runner['runner_subprocess']
    return {
        'normalized_outcome': runner['normalized_outcome'],
        'test_overrides': runner.get('test_overrides'),
        'error': runner.get('error'),
        'poll_stop_reason': sub.get('poll_stop_reason'),
        'exit_requested': sub.get('exit_requested'),
        'termination_request': sub.get('termination_request'),
        'term_signal': sub.get('term_signal'),
        'exit_code': sub.get('exit_code'),
        'reaped': sub.get('reaped'),
        'done_observed': sub.get('done_observed'),
        'partial_steps': sub.get('partial_steps'),
        'progress': (sub.get('worker_evidence') or {}).get('progress'),
    }


def observe_target(target):
    """The test's own view of the native effect, taken before any JSON is read."""
    try:
        info = target.lstat()
    except FileNotFoundError:
        return {'path': str(target), 'exists': False}
    return {'path': str(target), 'exists': True, 'regular': stat.S_ISREG(info.st_mode),
            'mode': oct(stat.S_IMODE(info.st_mode)), 'size': info.st_size, 'inode': info.st_ino}


def cleanup_staging(staging, envelope, artifacts):
    witnessed, reason = worker_exit_witness(envelope)
    record = {'staging': str(staging), 'worker_exit_witnessed': witnessed, 'witness': reason,
              'removed': False, 'error': None}
    if witnessed:
        try:
            shutil.rmtree(staging)
            record['removed'] = True
        except OSError as exc:
            record['error'] = f'staging removal failed: {exc}'
    else:
        record['error'] = (f'{reason}; staging retained at {staging}; confirm no pw-probe-runner '
                           'remains before removing it')
    (artifacts / 'cleanup.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return record['error']


def step(envelope, step_id):
    return next(s for s in envelope['data']['runner_result']['steps'] if s['step_id'] == step_id)


def check_setup(rc, seen, spec):
    """The boundary was reached: the worker died by signal with slot 1 started and unpublished."""
    assert rc == 1, f'setup: expected CLI failure exit 1, got {rc}'
    assert seen['test_overrides'] == spec['_test_overrides'], f'setup: override not echoed: {seen}'
    assert seen['poll_stop_reason'] == 'child_reaped', f'setup: the host did not reap a dead worker: {seen}'
    assert seen['term_signal'] == 9 and seen['exit_code'] is None and seen['reaped'] is True, f'setup: {seen}'
    assert seen['done_observed'] is False and seen['partial_steps'] is True, f'setup: {seen}'
    assert seen['progress'] == STARTED_ATTEMPT_1, f'setup: last progress is not attempt 1 started: {seen}'


def check_host_account(seen, diagnostics):
    """The host records its own observations and invents no request or cause."""
    assert seen['normalized_outcome'] == 'runner_failed', seen
    assert seen['termination_request'] is None, f'invented termination request: {seen}'
    error = seen['error'] or ''
    assert 'SIGKILL' not in error or 'host requested' not in error, f'host claims a kill it did not request: {error}'
    assert diagnostics['process_disposition'] == 'signaled', diagnostics
    cause = diagnostics.get('termination_cause')
    assert cause == 'unknown', f'self-signal must stay unknown, got {cause!r}'
    for key in ('sandbox_caused_termination', 'policy_caused_termination'):
        assert diagnostics.get(key) is not True, diagnostics


def check_completed(completed):
    attempt, comparison = completed['attempt'], completed.get('comparison') or {}
    assert attempt.get('outcome') == 'ok' and attempt.get('result_source') == 'worker', attempt
    assert attempt.get('rc') == 0 and attempt.get('missing_reason') is None, attempt
    assert attempt.get('lifecycle', {}).get('summary') == 'completed', attempt
    assert comparison.get('observation') == 'succeeded', comparison
    assert not any(l.startswith('attempt') for l in comparison.get('limitations', [])), comparison


def check_withheld(row, summary, limitation):
    attempt, comparison = row['attempt'], row['comparison']
    assert attempt['outcome'] == MISSING, attempt
    assert attempt['rc'] == -1 and attempt['errno'] is None, attempt
    assert 'native_rc' not in attempt, attempt
    assert attempt['result_source'] == 'synthetic' and attempt['missing_reason'] == 'slot_incomplete', attempt
    assert attempt.get('observed_path') is None, attempt
    assert attempt['lifecycle']['summary'] == summary, attempt['lifecycle']
    assert (comparison['observation'], comparison['observation_basis']) == ('unavailable', 'no_completed_worker_result'), comparison
    lifecycle_limits = [l for l in comparison['limitations'] if l.startswith('attempt:')]
    assert lifecycle_limits == [limitation], comparison
    error = (attempt.get('error') or '').lower()
    assert not any(word in error for word in FORBIDDEN_ERROR_WORDS), f'error text infers execution: {attempt}'


def main():
    pw, directory = sys.argv[1:]
    artifacts = Path(directory).resolve() / 'killed_before_publication'
    artifacts.mkdir(parents=True, exist_ok=False)
    staging = Path(tempfile.mkdtemp(prefix='pw-kill-before-publish-', dir='/private/tmp'))
    (artifacts / 'staging.json').write_text(json.dumps({'staging': str(staging)}) + '\n')
    target = staging / 'created.txt'
    before = observe_target(target)
    assert before == {'path': str(target), 'exists': False}, f'setup: target exists before the run: {before}'
    spec = specimen(target)
    envelope, rc, primary = None, None, None
    try:
        with RunCapture(pw, artifacts, spec, cli_args=CLI_ARGS) as run:
            rc = run.wait(timeout=HARNESS_WAIT_SECONDS)
            # Independent observation first: the native effect is read from the
            # file system, not from the reply.
            after = observe_target(target)
            (artifacts / 'observations.json').write_text(
                json.dumps({'before': before, 'after': after}, indent=2) + '\n', encoding='utf-8')
            envelope = run.load_json()
            print(f'elapsed {run.elapsed_seconds:.2f}s', flush=True)
    except BaseException as exc:
        primary = exc
    note = cleanup_staging(staging, envelope, artifacts)
    if primary is not None:
        if note:
            print(f'cleanup: {note}', file=sys.stderr, flush=True)
        raise primary
    if note:
        raise AssertionError(note)

    seen = witnesses(envelope)
    diagnostics = envelope['data']['runner_sandbox_diagnostics']
    (artifacts / 'witnesses.json').write_text(json.dumps(seen, indent=2) + '\n', encoding='utf-8')
    (artifacts / 'diagnostics.json').write_text(json.dumps(diagnostics, indent=2) + '\n', encoding='utf-8')

    assert after['exists'] and after['regular'] and after['size'] == 0 and after['mode'] == '0o600', \
        f'the native create did not happen as expected: {after}'
    print('independent: the worker created the file', flush=True)

    check_setup(rc, seen, spec)
    print('setup: worker reaped with SIGKILL after slot 1 started and before it published', flush=True)

    problems = consumer.validate(envelope)
    assert not problems, problems
    check_host_account(seen, diagnostics)
    check_completed(step(envelope, 'prefix'))
    check_withheld(step(envelope, 'created'), 'started_without_result', 'attempt:started_without_result')
    check_withheld(step(envelope, 'after'), 'not_reached', 'attempt:not_reached')
    # The created path did not exist when the host planned its queries, so the
    # query channel is the documented unavailable prediction; that is separate
    # evidence from the withheld attempt result and must not be confused with it.
    created = step(envelope, 'created')
    query = created['sandbox_check']
    assert query['outcome'] == 'prediction_unavailable' and query['rc'] == -1, query
    assert query['result_source'] == 'synthetic' and query['missing_reason'] == 'query_not_requested', query
    assert created['comparison']['order'] == 'unestablished', created['comparison']
    assert 'query_plan:path_unresolved_at_planning' in created['comparison']['limitations'], created['comparison']
    after = step(envelope, 'after')
    assert after['sandbox_check']['result_source'] == 'validator' and after['comparison']['order'] == 'query_first', after
    print('reply: unpublished result withheld; prefix kept; suffix not reached', flush=True)

    findings = lifecycle_oracle.check_record(envelope)
    (artifacts / 'oracle_findings.json').write_text(json.dumps(findings, indent=2) + '\n', encoding='utf-8')
    assert not findings, f'oracle findings {findings}'
    view = read_lifecycle(envelope)
    assert view['reporting'] == 'reported', (view['reporting'], view['malformed'])
    assert summaries(view) == ['completed', 'started_without_result', 'not_reached'], summaries(view)
    print('lifecycle: oracle agrees; summaries completed, started_without_result, not_reached', flush=True)


if __name__ == '__main__':
    main()

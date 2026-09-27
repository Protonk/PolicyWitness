"""A1: host cleanup after a deadline is reported as a cause.

Disposition record plan, area A, wave 1 (controller/DISPOSITION-RECORD-PLAN.md).
A two-step plan first opens a FIFO that has no writer, so attempt 0 blocks
inside the worker until the host's sentinel deadline fires. The host requests
SIGKILL, reaps signal 9 and publishes each observation in runner_subprocess.
The controller must project them as
runner_sandbox_diagnostics.termination_cause == HOST_SENTINEL_DEADLINE.
Today it reports 'unknown', discarding the host's own termination record.

Timing is equipment, not the oracle: worker_timeout_ms shortens the host
deadline. The check asserts the echoed override and the raw witnesses before
the behavioral assertion, so a run that never reached the FIFO boundary fails
as setup, not as behavior. The per-step compatibility triples are recorded as
an artifact for A2 without being asserted.

Test-owned cleanup: the FIFO lives in staging this check creates under
/private/tmp and never opens. Staging is removed only after the host's own
witness (reaped: true, or no worker spawned) establishes that no worker can
still be blocked on it; otherwise it is retained and named separately from any
primary assertion failure.
"""
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from lifecycle_contract import HOST_SENTINEL_DEADLINE
from run_capture import RunCapture

OVERRIDES = {'worker_timeout_ms': 2000}
CLI_TIMEOUT_MS = 20000
HARNESS_WAIT_SECONDS = 60  # bounded, and longer than the CLI's own deadline

# PW_OP_ATTEMPT (9) at PW_PROGRESS_STARTED (1) for item 0, encoded by
# pw_progress as (op << 24) | (phase << 20) | (index + 1).
STARTED_ATTEMPT_0 = {'operation': 9, 'phase': 1, 'index': 0, 'raw': (9 << 24) | (1 << 20) | 1}


def read_step(step_id, target):
    return {'step_id': step_id,
            'sandbox_check': {'operation': 'file-read-data',
                              'filter': {'kind': 'path', 'value': str(target)}},
            'attempt': {'kind': 'file', 'action': 'open_read', 'target': str(target)}}


def specimen(fifo):
    return {
        'schema_version': 1, 'specimen_id': 'attempt_in_flight_at_deadline',
        'policy': {'format': 'sbpl', 'sbpl_source': '(version 1) (allow default)'},
        'probe_plan': [read_step('fifo', fifo), read_step('hosts', '/etc/hosts')],
        '_test_overrides': dict(OVERRIDES),
    }


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


def compatibility_triples(envelope):
    rows = []
    for step in envelope['data']['runner_result']['steps']:
        attempt = step['attempt']
        limitations = (step.get('comparison') or {}).get('limitations', [])
        rows.append({'step_id': step['step_id'], 'outcome': attempt.get('outcome'),
                     'missing_reason': attempt.get('missing_reason'),
                     'result_source': attempt.get('result_source'),
                     'attempt_limitations': [l for l in limitations if l.startswith('attempt')]})
    return rows


def host_witnessed_worker_exit(envelope):
    """True when the host's own record says no worker can still be running."""
    runner = ((envelope or {}).get('data') or {}).get('runner_result') or {}
    sub = runner.get('runner_subprocess')
    if not sub or not sub.get('pid'):
        return True  # no worker was spawned
    return sub.get('reaped') is True


def check_setup(rc, seen, spec):
    """The FIFO boundary was reached and the host recorded its own cleanup."""
    assert rc == 1, f'setup: expected CLI failure exit 1, got {rc}'
    assert seen['test_overrides'] == spec['_test_overrides'], f'setup: override not echoed: {seen}'
    assert seen['normalized_outcome'] == 'runner_timeout', f'setup: {seen}'
    assert seen['poll_stop_reason'] == 'sentinel_deadline', f'setup: {seen}'
    assert seen['exit_requested'] is True, f'setup: {seen}'
    assert seen['termination_request'] == {'rc': 0, 'signal': 9}, f'setup: {seen}'
    assert seen['term_signal'] == 9 and seen['exit_code'] is None and seen['reaped'] is True, f'setup: {seen}'
    assert seen['done_observed'] is False and seen['partial_steps'] is True, f'setup: {seen}'
    assert seen['progress'] == STARTED_ATTEMPT_0, f'setup: last progress is not attempt 0 started: {seen}'


def check_unaffected(seen, diagnostics):
    """Preservation: summary, error clauses and final status stay as today."""
    error = seen['error'] or ''
    assert 'sentinel deadline' in error and 'host requested SIGKILL' in error, seen
    assert diagnostics['process_disposition'] == 'signaled', diagnostics


def attributes_to_sandbox(value):
    text = str(value).lower()
    return any(word in text for word in ('sandbox', 'policy', 'kernel'))


def check_cause(seen, diagnostics):
    """The red: the witnessed host cleanup must be projected as the cause."""
    cause = diagnostics.get('termination_cause')
    assert not attributes_to_sandbox(cause), \
        f'termination_cause {cause!r} attributes the signal to the sandbox; witnesses: {seen}'
    assert cause == HOST_SENTINEL_DEADLINE, (
        f"termination_cause {cause!r} discards the host's own termination record; expected "
        f'{HOST_SENTINEL_DEADLINE!r} from sentinel_deadline + termination_request rc 0 signal 9 + '
        f'reaped term_signal 9; witnesses: {seen}')


def cleanup_staging(staging, worker_absent, out):
    record = {'staging': str(staging), 'worker_absent_by_host_witness': worker_absent,
              'removed': False, 'error': None}
    if worker_absent:
        try:
            shutil.rmtree(staging)
            record['removed'] = True
        except OSError as exc:
            record['error'] = f'staging removal failed: {exc}'
    else:
        record['error'] = ('worker exit not witnessed by the host (reaped is not true); staging '
                           f'retained at {staging}; confirm no pw-probe-runner remains before removing it')
    (out / 'cleanup.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return record['error']


def main():
    pw, directory = sys.argv[1:]
    out = Path(directory).resolve()
    staging = Path(tempfile.mkdtemp(prefix='pw-in-flight-', dir='/private/tmp'))
    fifo = staging / 'blocker.fifo'
    os.mkfifo(fifo, 0o600)
    assert stat.S_ISFIFO(fifo.lstat().st_mode), f'setup: {fifo} is not a FIFO'
    spec = specimen(fifo)
    worker_absent = False
    primary = None
    try:
        cli_args = ['--no-log-capture', '--timeout-ms', str(CLI_TIMEOUT_MS)]
        with RunCapture(pw, out, spec, cli_args=cli_args) as run:
            rc = run.wait(timeout=HARNESS_WAIT_SECONDS)
            envelope = run.load_json()
            worker_absent = host_witnessed_worker_exit(envelope)
            seen = witnesses(envelope)
            diagnostics = envelope['data']['runner_sandbox_diagnostics']
            for name, value in (('witnesses.json', seen), ('diagnostics.json', diagnostics),
                                ('compatibility_triples.json', compatibility_triples(envelope))):
                (out / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
            print(f'elapsed {run.elapsed_seconds:.2f}s; raw witnesses recorded in {out}', flush=True)
            check_setup(rc, seen, spec)
            print('setup: FIFO boundary reached; deadline, SIGKILL request and reap witnessed', flush=True)
            check_unaffected(seen, diagnostics)
            print('unaffected: runner_timeout, error clauses and signaled disposition preserved', flush=True)
            check_cause(seen, diagnostics)
    except BaseException as exc:  # keep the primary failure visible beside cleanup
        primary = exc
    note = cleanup_staging(staging, worker_absent, out)
    if primary is not None:
        if note:
            print(f'cleanup: {note}', file=sys.stderr, flush=True)
        raise primary
    if note:
        raise AssertionError(note)
    print(f'termination_cause == {HOST_SENTINEL_DEADLINE!r}: witnessed host cleanup projected')


if __name__ == '__main__':
    main()

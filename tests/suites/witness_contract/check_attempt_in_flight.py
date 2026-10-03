"""Area A of the disposition record plan: live loss of known facts.

Three specimens run through RunCapture with --no-log-capture, all under
(version 1) (allow default):

- a1: a FIFO with no writer, then /etc/hosts, with worker_timeout_ms 2000.
  Attempt 0 blocks inside the worker until the host's sentinel deadline; the
  host requests SIGKILL, reaps signal 9 and publishes each observation. The
  controller must project them as termination_cause == HOST_SENTINEL_DEADLINE
  (A1, the wave-1 red; today it reports 'unknown').
- a3: /etc/hosts, the FIFO, /etc/hosts. The completed first result must survive
  the termination with an attempt in flight (A3 preservation half).
- a4: /etc/hosts with worker_timeout_ms 300 and worker_post_apply_hang_ms 800.
  The deadline fires and the worker exits 0 during grace; deadline, clean exit
  and the completed result all survive and no kill is invented (A4
  preservation half).

Timing is equipment, not the oracle: each specimen's overrides make a boundary
reachable, and the check asserts the echoed overrides and the raw witnesses
before any behavioral assertion, so a run that did not reach its boundary fails
as setup. Preservation assertions run before the red so their results are
visible in the log. The per-step compatibility triples are recorded for A2
without assertion; the wave-2 semantic claims (A2, A3, A4) stay in the plan.

Test-owned cleanup: each FIFO lives in staging this check creates under
/private/tmp and never opens. Staging is removed only when the envelope's own
host witness, runner_subprocess.reaped == true with a valid worker PID,
establishes the worker is gone
(tests/lib/worker_exit_witness.py); otherwise it is retained and named
separately from any primary failure. Setup failure before CLI launch is settled
from the test's own non-spawn observation.
"""
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import lifecycle_contract as C
from lifecycle_contract import HOST_SENTINEL_DEADLINE
import lifecycle_oracle
from lifecycle_adapter import read_lifecycle, summaries
from run_capture import RunCapture
from worker_exit_witness import worker_exit_witness

CLI_ARGS = ['--no-log-capture', '--timeout-ms', '20000']
HARNESS_WAIT_SECONDS = 60  # bounded, and longer than the CLI's own deadline
FIFO_OVERRIDES = {'worker_timeout_ms': 2000}
GRACE_OVERRIDES = {'worker_timeout_ms': 300, 'worker_post_apply_hang_ms': 800}
POLICY = {'format': 'sbpl', 'sbpl_source': '(version 1) (allow default)'}


def progress_word(operation, phase, index=None):
    """pw_progress encoding: (op << 24) | (phase << 20) | (index + 1); no item when index is None."""
    word = (operation << 24) | (phase << 20) | (0 if index is None else index + 1)
    decoded = {'operation': operation, 'phase': phase, 'raw': word}
    if index is not None:
        decoded['index'] = index
    return decoded


def started_attempt(index):
    return progress_word(9, 1, index)  # PW_OP_ATTEMPT, PW_PROGRESS_STARTED


FINISHED_RETURNED = progress_word(10, 2)


def read_step(step_id, target):
    return {'step_id': step_id,
            'sandbox_check': {'operation': 'file-read-data',
                              'filter': {'kind': 'path', 'value': str(target)}},
            'attempt': {'kind': 'file', 'action': 'open_read', 'target': str(target)}}


def specimen(specimen_id, plan, overrides):
    return {'schema_version': 3, 'specimen_id': specimen_id, 'policy': dict(POLICY),
            'probe_plan': plan, '_test_overrides': dict(overrides)}


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


def cleanup_staging(staging, envelope, artifacts, *, launch_attempted):
    witnessed, reason = worker_exit_witness(envelope)
    if not launch_attempted:
        reason = 'the test did not attempt CLI launch; it could not spawn a worker'
    record = {'staging': str(staging), 'worker_exit_witnessed': witnessed, 'witness': reason,
              'cli_launch_attempted': launch_attempted,
              'removed': False, 'error': None}
    if witnessed or not launch_attempted:
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


def execute(pw, out, name, make_spec, *, fifo=False):
    """Own staging from setup through capture; retain it when worker exit is unknown."""
    artifacts = out / name
    # Refuse reuse before creating staging or overwriting any prior evidence.
    artifacts.mkdir(parents=True, exist_ok=False)
    envelope, rc, primary = None, None, None
    staging = None
    launch_attempted = False
    try:
        target = None
        if fifo:
            staging = Path(tempfile.mkdtemp(prefix='pw-in-flight-', dir='/private/tmp'))
            # Keep the recovery path even if FIFO setup or capture later fails.
            (artifacts / 'staging.json').write_text(json.dumps({'staging': str(staging)}) + '\n')
            target = staging / 'blocker.fifo'
            os.mkfifo(target, 0o600)
            assert stat.S_ISFIFO(target.lstat().st_mode), f'setup: {target} is not a FIFO'
        spec = make_spec(target)
        capture = RunCapture(pw, artifacts, spec, cli_args=CLI_ARGS)
        launch_attempted = True
        with capture as run:
            rc = run.wait(timeout=HARNESS_WAIT_SECONDS)
            envelope = run.load_json()
            print(f'{name}: elapsed {run.elapsed_seconds:.2f}s', flush=True)
    except BaseException as exc:  # keep the primary failure visible beside cleanup
        primary = exc
    note = None
    if staging is not None:
        try:
            note = cleanup_staging(staging, envelope, artifacts, launch_attempted=launch_attempted)
        except Exception as exc:
            # Metadata I/O failures must not replace the original capture failure.
            note = f'cleanup reporting failed for staging {staging}: {exc}; inspect staging.json and the capture'
    if primary is not None:
        if note:
            print(f'{name}: cleanup: {note}', file=sys.stderr, flush=True)
        raise primary
    if note:
        raise AssertionError(f'{name}: {note}')
    return rc, envelope, artifacts, spec


def record(artifacts, envelope):
    seen = witnesses(envelope)
    diagnostics = envelope['data']['runner_sandbox_diagnostics']
    for filename, value in (('witnesses.json', seen), ('diagnostics.json', diagnostics),
                            ('compatibility_triples.json', compatibility_triples(envelope))):
        (artifacts / filename).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return seen, diagnostics


def step(envelope, step_id):
    return next(s for s in envelope['data']['runner_result']['steps'] if s['step_id'] == step_id)


def check_kill_after_deadline(name, rc, seen, spec, progress):
    """Setup for the FIFO specimens: the boundary was reached and the host recorded its cleanup."""
    assert rc == 1, f'{name} setup: expected CLI failure exit 1, got {rc}'
    assert seen['test_overrides'] == spec['_test_overrides'], f'{name} setup: override not echoed: {seen}'
    assert seen['normalized_outcome'] == 'runner_timeout', f'{name} setup: {seen}'
    assert seen['poll_stop_reason'] == 'sentinel_deadline', f'{name} setup: {seen}'
    assert seen['exit_requested'] is True, f'{name} setup: {seen}'
    assert seen['termination_request'] == {'rc': 0, 'signal': 9}, f'{name} setup: {seen}'
    assert seen['term_signal'] == 9 and seen['exit_code'] is None and seen['reaped'] is True, \
        f'{name} setup: {seen}'
    assert seen['done_observed'] is False and seen['partial_steps'] is True, f'{name} setup: {seen}'
    assert seen['progress'] == progress, f'{name} setup: last progress is not {progress}: {seen}'


def check_deadline_preserved(name, seen, diagnostics):
    """Preservation: summary, error clauses and final status stay as today."""
    error = seen['error'] or ''
    assert 'sentinel deadline' in error and 'host requested SIGKILL' in error, (name, seen)
    assert diagnostics['process_disposition'] == 'signaled', (name, diagnostics)


def check_completed(name, completed):
    """A completed worker result keeps its native values and its agreement."""
    attempt, comparison = completed['attempt'], completed.get('comparison') or {}
    assert attempt.get('outcome') == 'ok', (name, attempt)
    assert attempt.get('result_source') == 'worker', (name, attempt)
    assert attempt.get('rc') == 0 and attempt.get('missing_reason') is None, (name, attempt)
    assert comparison.get('observation') == 'succeeded', (name, comparison)
    assert not any(l.startswith('attempt') for l in comparison.get('limitations', [])), (name, comparison)


def check_grace_exit(rc, seen, spec, diagnostics, envelope):
    """A4: the deadline fired and the worker exited 0 during grace; everything survives."""
    assert rc == 1, f'a4 setup: expected CLI failure exit 1, got {rc}'
    assert seen['test_overrides'] == spec['_test_overrides'], f'a4 setup: override not echoed: {seen}'
    assert seen['normalized_outcome'] == 'runner_timeout', f'a4 setup: {seen}'
    assert seen['poll_stop_reason'] == 'sentinel_deadline' and seen['exit_requested'] is True, \
        f'a4 setup: {seen}'
    assert seen['exit_code'] == 0 and seen['reaped'] is True and seen['done_observed'] is True, \
        f'a4 setup: the worker did not exit cleanly during grace (timing): {seen}'
    # Preservation: deadline and clean exit coexist; no intervention is invented.
    assert seen['termination_request'] is None and seen['term_signal'] is None, f'a4: invented kill: {seen}'
    error = seen['error'] or ''
    assert 'sentinel deadline' in error and 'no termination requested' in error, ('a4', seen)
    assert 'SIGKILL' not in error, ('a4', seen)
    assert seen['partial_steps'] is False and seen['progress'] == FINISHED_RETURNED, ('a4', seen)
    check_completed('a4', step(envelope, 'hosts'))
    assert diagnostics['process_disposition'] == 'clean_exit', ('a4', diagnostics)
    assert diagnostics.get('termination_cause') is None, ('a4', diagnostics)


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


def check_wave2(name, envelope, expected_summaries, artifacts):
    """A2, A3 and A4 semantic claims through the adapter and the independent oracle.

    The oracle reads the record under the contract manifest's exact version;
    another version is its own finding, not a behavioral failure.
    """
    findings = lifecycle_oracle.check_record(envelope)
    (artifacts / 'oracle_findings.json').write_text(json.dumps(findings, indent=2) + '\n', encoding='utf-8')
    assert not findings, f'{name}: oracle findings {findings}'
    view = read_lifecycle(envelope)
    assert view['reporting'] == 'reported', (name, view['reporting'], view['malformed'])
    assert summaries(view) == expected_summaries, (name, summaries(view), expected_summaries)
    return view


def main():
    pw, directory = sys.argv[1:]
    out = Path(directory).resolve()

    rc, envelope_a1, artifacts, spec_a1 = execute(pw, out, 'a1', lambda fifo: specimen(
        'a1_fifo_then_file', [read_step('fifo', fifo), read_step('hosts', '/etc/hosts')],
        FIFO_OVERRIDES), fifo=True)
    envelope = envelope_a1
    seen_a1, diagnostics_a1 = record(artifacts, envelope)
    check_kill_after_deadline('a1', rc, seen_a1, spec_a1, started_attempt(0))
    check_deadline_preserved('a1', seen_a1, diagnostics_a1)
    print('a1: FIFO boundary reached; deadline, SIGKILL request and reap witnessed; summary preserved', flush=True)

    rc, envelope_a3, artifacts, spec_a3 = execute(pw, out, 'a3', lambda fifo: specimen(
        'a3_completed_prefix_then_fifo',
        [read_step('first', '/etc/hosts'), read_step('fifo', fifo), read_step('after', '/etc/hosts')],
        FIFO_OVERRIDES), fifo=True)
    envelope = envelope_a3
    seen_a3, diagnostics_a3 = record(artifacts, envelope)
    check_kill_after_deadline('a3', rc, seen_a3, spec_a3, started_attempt(1))
    check_deadline_preserved('a3', seen_a3, diagnostics_a3)
    check_completed('a3', step(envelope, 'first'))
    print('a3: completed prefix survives termination with an attempt in flight', flush=True)

    rc, envelope_a4, artifacts, spec_a4 = execute(pw, out, 'a4', lambda _: specimen(
        'a4_deadline_then_voluntary_exit', [read_step('hosts', '/etc/hosts')], GRACE_OVERRIDES))
    envelope = envelope_a4
    seen_a4, diagnostics_a4 = record(artifacts, envelope)
    check_grace_exit(rc, seen_a4, spec_a4, diagnostics_a4, envelope)
    print('a4: deadline and voluntary clean exit coexist; completed result survives; no kill invented', flush=True)

    check_cause(seen_a1, diagnostics_a1)
    print(f'a1: termination_cause == {HOST_SENTINEL_DEADLINE!r}: witnessed host cleanup projected', flush=True)

    # Wave 2: the account itself, asserted after the wave-1 red so that red stays visible first.
    check_wave2('a1', envelope_a1, ['started_without_result', 'not_reached'], out / 'a1')
    check_wave2('a3', envelope_a3, ['completed', 'started_without_result', 'not_reached'], out / 'a3')
    view_a4 = check_wave2('a4', envelope_a4, ['completed'], out / 'a4')
    assert view_a4['projections']['stop_reason'] == 'sentinel_deadline', view_a4['projections']
    assert view_a4['projections']['process_disposition'] == 'clean_exit', view_a4['projections']
    assert view_a4['projections']['termination_cause'] is None, view_a4['projections']
    print('a2/a3/a4: lifecycle claims, projections and stop reason agree with the independent oracle')


if __name__ == '__main__':
    main()

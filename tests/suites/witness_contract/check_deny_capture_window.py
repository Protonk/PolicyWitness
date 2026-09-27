"""The live observer is asked for the whole client interval.

The specimen denies one read, holds two exec children to their worker deadlines,
then denies another read, so the first denial is well over ten seconds older
than the reply. Allowed metadata queries avoid generating read-denial records
before the attempts. Real ``log show`` must accept and mirror the independently
computed bounds. Missing kernel records are recorded as unavailable evidence.

An independent control replays the retired trailing interval (the ten seconds
before the client's end) through the same embedded observer against the same
log store. Event timestamps, when present, establish interval membership;
path names do not establish timing. Deterministic Rust controls use a fixed
event corpus to require early/late inclusion and exclusion at both bounds.

The final denied read is the minimum witness: it happened last, inside the
scanned span, so a log store that holds no record of it fails the case with a
named reason after every artifact is written. The envelope must also list each
unrecorded permission failure beside its correlation status.
"""
import errno
import json
import re
import secrets
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture
from consumer import recover_evidence, validate_evidence_shape

STAMP = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\+0000$')
RETIRED_LOOKBACK_SECONDS = 10
WINDOW_FLAGS = ('event_timestamps_available', 'exact_run_membership', 'step_ordering', 'pid_reuse_protection')


def stamp(seconds):
    """Independent oracle for the controller's formatter: UTC, whole seconds, explicit offset."""
    return datetime.fromtimestamp(seconds, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S+0000')


def timed_reads(events, pid):
    reads = []
    for index, event in enumerate(events):
        if event.get('pid') != pid or event.get('operation') != 'file-read-data':
            continue
        # Test-only interpretation of the actual syslog timestamp. Production
        # continues to expose the raw line without structured temporal claims.
        prefix = ' '.join(event['raw_line'].split()[:2])
        at = datetime.strptime(prefix, '%Y-%m-%d %H:%M:%S.%f%z').timestamp()
        reads.append({'event_index': index, 'path': event['path'], 'at': at,
                      'raw_line': event['raw_line']})
    return reads


def main():
    pw, directory = sys.argv[1:]
    pw = Path(pw)
    out = Path(directory)
    observer = pw.parent / 'sandbox-log-observer'
    assert observer.is_file(), f'embedded observer missing: {observer}'
    with tempfile.TemporaryDirectory(prefix='pw-window-', dir='/private/tmp') as work:
        early = Path(work) / secrets.token_hex(12)
        late = Path(work) / secrets.token_hex(12)
        for target in (early, late):
            target.write_bytes(secrets.token_bytes(16))
        ids = {name: secrets.token_hex(8) for name in ('early', 'hold_a', 'hold_b', 'late')}

        def read_step(name, target):
            return {'step_id': ids[name],
                    'sandbox_check': {'operation': 'file-read-metadata', 'filter': {'kind': 'path', 'value': str(target)}},
                    'attempt': {'kind': 'file', 'action': 'open_read', 'target': str(target)}}

        def hold_step(name):
            # /bin/sleep outlives the worker's exec deadline, which SIGKILLs it.
            return {'step_id': ids[name],
                    'sandbox_check': {'operation': 'process-exec*', 'filter': {'kind': 'path', 'value': '/bin/sleep'}},
                    'attempt': {'kind': 'exec', 'action': 'spawn', 'target': '/bin/sleep', 'args': ['120']}}

        specimen = {
            'schema_version': 1, 'specimen_id': secrets.token_hex(12),
            'policy': {'format': 'sbpl',
                       'sbpl_source': '(version 1)(allow default)'
                                      '(deny file-read-data (literal (param "EARLY")))'
                                      '(deny file-read-data (literal (param "LATE")))',
                       'params': {'EARLY': str(early), 'LATE': str(late)}},
            'probe_plan': [read_step('early', early), hold_step('hold_a'), hold_step('hold_b'), read_step('late', late)],
        }
        run = RunCapture(pw, out / 'run', specimen, cli_args=['--timeout-ms', '120000'])
        with run:
            rc = run.wait(timeout=150)
            envelope = run.load_json()

    assert rc == 0, rc
    assert envelope['schema_version'] >= 2, envelope['schema_version']
    data = envelope['data']
    assert 'log_last' not in data, data.keys()
    runner = data['runner_result']
    assert runner['schema_version'] >= 7, runner
    assert runner['normalized_outcome'] == 'ok', runner
    worker = runner['runner_subprocess']
    assert worker['exit_code'] == 0 and worker.get('term_signal') is None, worker
    steps = {step['step_id']: step for step in runner['steps']}
    assert list(steps) == [ids[name] for name in ('early', 'hold_a', 'hold_b', 'late')], list(steps)
    for name in ('early', 'late'):
        step = steps[ids[name]]
        assert step['sandbox_check']['outcome'] == 'allow', step
        attempt = step['attempt']
        assert attempt['outcome'] == 'open_failed' and attempt['errno'] in (errno.EPERM, errno.EACCES), attempt
    for name in ('hold_a', 'hold_b'):
        attempt = steps[ids[name]]['attempt']
        assert attempt['child_pid'] > 0 and attempt['child_term_signal'] == 9, attempt
        assert 'deadline' in (attempt.get('error') or ''), attempt

    # The run outlasted the retired lookback by more than the whole-second slack.
    client = data['runner_client']
    span_ms = client['ended_at_unix_ms'] - client['started_at_unix_ms']
    assert span_ms > (RETIRED_LOOKBACK_SECONDS + 2) * 1000, span_ms

    capture = data['sandbox_log_capture']
    assert isinstance(capture, dict), 'capture must be attempted when the worker PID is known'
    window = capture['window']
    assert window['kind'] == 'runner_client_span' and 'last' not in window, window
    assert window['started_at_unix_ms'] == client['started_at_unix_ms'], (window, client)
    assert window['ended_at_unix_ms'] == client['ended_at_unix_ms'], (window, client)
    start_s = client['started_at_unix_ms'] // 1000
    end_s = max((client['ended_at_unix_ms'] + 999) // 1000, start_s + 1)
    assert (window['start'], window['end']) == (stamp(start_s), stamp(end_s)), window
    assert STAMP.match(window['start']) and STAMP.match(window['end']), window
    for key in WINDOW_FLAGS:
        assert window[key] is False, window
    if capture['capture_status'] == 'blocked':
        raise AssertionError('unified log refused (%r); run from an unsandboxed session, see '
                             'tests/README.md → Sandboxed automation harnesses' % capture.get('blocked_reason'))
    assert capture['capture_status'] == 'captured', capture
    mirrored = capture['observer']['data']
    assert mirrored['pid'] == worker['pid'] and mirrored['process_name'] == 'pw-probe-runner', mirrored
    assert mirrored['last'] is None, mirrored
    assert (mirrored['start'], mirrored['end']) == (window['start'], window['end']), mirrored
    # The real tool accepted the generated strings; a format regression fails here.
    assert mirrored['log_rc'] == 0 and mirrored['log_error'] is None, mirrored

    events = capture['deny_events']
    reads = timed_reads(events, worker['pid'])
    associations = {item['event_index']: item for item in capture['step_denies']}
    expected_steps = {str(early): ids['early'], str(late): ids['late']}
    for read in reads:
        assert start_s <= read['at'] <= end_s, read
        assert read['path'] in expected_steps, read
        association = associations[read['event_index']]
        assert association['candidate_step_ids'] == [expected_steps[read['path']]], association
        assert association['association'] == 'candidate', association
    diagnostics = data['runner_sandbox_diagnostics']
    matches = [i for i, event in enumerate(events) if event.get('pid') == worker['pid']]
    assert diagnostics['capture_status'] == 'captured', diagnostics
    assert diagnostics['correlation_status'] == ('pid_match' if matches else 'no_match'), diagnostics
    assert diagnostics['first_deny'] == ({'event_index': matches[0]} if matches else None), diagnostics
    assert not validate_evidence_shape(envelope), validate_evidence_shape(envelope)
    answers = recover_evidence(envelope)
    assert answers['denials']['window'] == window
    (out / 'consumer-answers.json').write_text(json.dumps(answers, indent=2) + '\n')

    # Control: the retired trailing interval, replayed against the same log store.
    retired_start = stamp(end_s - RETIRED_LOOKBACK_SECONDS)
    argv = [str(observer), '--pid', str(worker['pid']), '--process-name', 'pw-probe-runner',
            '--start', retired_start, '--end', window['end'], '--format', 'json']
    control = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    (out / 'retired-window.json').write_text(control.stdout)
    (out / 'retired-window.stderr').write_text(control.stderr)
    assert control.returncode == 0, control.stderr
    retired = json.loads(control.stdout)['data']
    assert retired['log_rc'] == 0 and retired['log_error'] is None, retired
    assert (retired['start'], retired['end'], retired['last']) == (retired_start, window['end'], None), retired
    retired_reads = timed_reads(retired['deny_events'], worker['pid'])
    for read in retired_reads:
        assert end_s - RETIRED_LOOKBACK_SECONDS <= read['at'] <= end_s, read
    # Only timestamped observations support a temporal claim. Neither scan is
    # required to contain a record for every denied attempt.
    older = [read for read in reads if read['at'] < end_s - RETIRED_LOOKBACK_SECONDS]
    assert not ({read['raw_line'] for read in older} & {read['raw_line'] for read in retired_reads})
    availability = {name: ('observed' if any(read['path'] == str(target) for read in reads)
                           else 'not_observed') for name, target in [('early', early), ('late', late)]}

    (out / 'observations.json').write_text(json.dumps({
        'span_ms': span_ms, 'window': window, 'retired_window': {'start': retired_start, 'end': window['end']},
        'run_bounded_reads': reads, 'retired_reads': retired_reads,
        'availability': availability, 'observed_events_outside_retired_window': older,
        'permission_failures_without_record': diagnostics['permission_failures_without_record'],
        'steps': ids}, indent=2) + '\n')
    print(f'window equals the client span ({span_ms} ms); real log show accepts both intervals; '
          f'live denial availability={availability}', flush=True)

    # The envelope names exactly the denied reads the log did not record.
    unrecorded = sorted(ids[name] for name in ('early', 'late') if availability[name] == 'not_observed')
    assert sorted(diagnostics['permission_failures_without_record']) == unrecorded, \
        (diagnostics['permission_failures_without_record'], unrecorded)
    if availability['late'] == 'not_observed':
        raise AssertionError('late denial unrecorded: the unified log holds no deny record for the worker\'s final '
                             'denied read inside the scanned span; see observations.json and retired-window.json')


if __name__ == '__main__':
    main()

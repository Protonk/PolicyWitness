"""Native denied attempts and padded scan bounds, independent of OS emission.

Each live invocation is checked on its own collection/cleanup facts. Completed
queries may be empty; documented budget exhaustion withholds correlation.
Returned records must satisfy interval and candidate checks, but do not prove
retrieval completeness. Supplied-text and archive controls require preservation.
The retired ten-second query is a separate observation, never a presence oracle.
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
from log_capture_contract import check_live_capture, check_observer_report

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


def checked_reads(capture, pid, start_s, end_s, expected_steps):
    # A bounded prefix may end inside a parsed path. Those diagnostic records
    # must not acquire complete-query membership or association claims.
    if capture['capture_status'] != 'captured':
        return []
    reads = timed_reads(capture['deny_events'], pid)
    associations = {item['event_index']: item for item in capture['step_denies']}
    for read in reads:
        assert start_s <= read['at'] <= end_s, read
        assert read['path'] in expected_steps, read
        association = associations[read['event_index']]
        assert association['candidate_step_ids'] == [expected_steps[read['path']]], association
        assert association['association'] == 'candidate', association
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
    assert window['pad_seconds'] == 2, window
    query_start_s = client['started_at_unix_ms'] // 1000 - 2
    query_end_s = (client['ended_at_unix_ms'] + 999) // 1000 + 2
    assert (window['start'], window['end']) == (stamp(query_start_s), stamp(query_end_s)), window
    assert STAMP.match(window['start']) and STAMP.match(window['end']), window
    for key in WINDOW_FLAGS:
        assert window[key] is False, window
    live_result = check_live_capture(envelope)
    complete = live_result['outcome'] == 'captured'

    expected_steps = {str(early): ids['early'], str(late): ids['late']}
    reads = checked_reads(capture, worker['pid'], query_start_s, query_end_s, expected_steps)
    diagnostics = data['runner_sandbox_diagnostics']
    assert not validate_evidence_shape(envelope), validate_evidence_shape(envelope)
    answers = recover_evidence(envelope)
    assert answers['denials']['window'] == window
    (out / 'consumer-answers.json').write_text(json.dumps(answers, indent=2) + '\n')

    # Control: the retired trailing interval, replayed against the same log store.
    retired_end_s = (client['ended_at_unix_ms'] + 999) // 1000
    retired_start_s = retired_end_s - RETIRED_LOOKBACK_SECONDS
    retired_start, retired_end = stamp(retired_start_s), stamp(retired_end_s)
    argv = [str(observer), '--pid', str(worker['pid']), '--process-name', 'pw-probe-runner',
            '--start', retired_start, '--end', retired_end, '--format', 'json']
    control = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    (out / 'retired-window.json').write_text(control.stdout)
    (out / 'retired-window.stderr').write_text(control.stderr)
    assert control.returncode == 0, control.stderr
    retired_envelope = json.loads(control.stdout)
    retired_cutoff = check_observer_report(retired_envelope, worker['pid'], retired_start, retired_end)
    retired = retired_envelope['data']
    retired_reads = timed_reads(retired['deny_events'], worker['pid']) if retired_cutoff is None else []
    for read in retired_reads:
        assert retired_start_s <= read['at'] <= retired_end_s, read
    # Compare observations for diagnostics only: no cross-query presence claim.
    older = [read for read in reads if read['at'] < retired_start_s]
    availability = {name: ('unavailable' if not complete else
                           'observed' if any(read['path'] == str(target) for read in reads)
                           else 'not_observed') for name, target in [('early', early), ('late', late)]}

    (out / 'observations.json').write_text(json.dumps({
        'span_ms': span_ms, 'window': window, 'live_result': live_result,
        'retired_cutoff': retired_cutoff, 'retired_window': {'start': retired_start, 'end': retired_end},
        'run_bounded_reads': reads, 'retired_reads': retired_reads,
        'availability': availability, 'observed_events_outside_retired_window': older,
        'first_seen_in_retired_query': ([r for r in retired_reads if r['raw_line'] not in {x['raw_line'] for x in reads}]
                                        if complete and retired_cutoff is None else None),
        'permission_failures_without_record': diagnostics['permission_failures_without_record'],
        'steps': ids}, indent=2) + '\n')
    print(f'window equals the padded client span ({span_ms} ms); collection={live_result["outcome"]}; '
          f'live denial availability={availability}', flush=True)

    if complete:
        # Absence describes this completed query, never absence of a denial.
        unrecorded = sorted(ids[name] for name in ('early', 'late') if availability[name] == 'not_observed')
        assert sorted(diagnostics['permission_failures_without_record']) == unrecorded, \
            (diagnostics['permission_failures_without_record'], unrecorded)


if __name__ == '__main__':
    main()
